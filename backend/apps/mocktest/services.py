import json
import re
import os
import secrets
import logging
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from .models import Question, MockTest, TestAttempt, Answer
from apps.roadmap.models import PYQ, Topic
from groq import Groq
from django.conf import settings
from common.utils.retry_utils import safe_llm_call

_SECURE_RNG = secrets.SystemRandom()
logger = logging.getLogger(__name__)


class MockTestService:
    _OPTION_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @staticmethod
    def create_mock_test(
        user, roadmap, day, topics, num_questions=10, duration_minutes=30
    ):
        topic_ids = sorted([t.id for t in topics])

        logger.debug("=== MOCKTEST DEBUG ===")
        logger.debug("Day: %s", day)
        logger.debug("Topics: %s", [t.name for t in topics])
        logger.debug("Num questions requested: %s", num_questions)

        # PRIMARY SOURCE: Get PYQs from roadmap.PYQ table - search ALL day topics
        main_topic = topics[0] if topics else None
        pyq_questions = MockTestService._get_pyq_questions(topics, num_questions) if topics else []

        logger.debug(
            "PYQ questions found in %s day topics: %s", len(topics), len(pyq_questions)
        )

        selected_questions = list(pyq_questions)  # Copy list
        remaining = num_questions - len(selected_questions)

        # SECONDARY SOURCE: existing question bank for these topics
        if remaining > 0 and topics:
            bank_questions = MockTestService._get_question_bank_questions(
                topics=topics, count=remaining, exclude_ids=[q.id for q in selected_questions]
            )
            logger.debug("Question-bank fallback found: %s", len(bank_questions))
            selected_questions.extend(bank_questions)
            remaining = num_questions - len(selected_questions)

        # FALLBACK: Use LLM to generate for remaining count, focusing on day topics
        llm_questions = []
        if remaining > 0:
            # Use day topics for LLM to keep relevance
            llm_topics = topics if len(topics) <= 3 else topics[:3]
            logger.info(
                "Generating %s questions via LLM for day topics: %s",
                remaining,
                [t.name for t in llm_topics],
            )
            llm_questions = MockTestService._generate_llm_questions_with_retry(
                topics=llm_topics, count=remaining
            )
            logger.debug("LLM questions generated: %s", len(llm_questions))
            selected_questions.extend(llm_questions)

        # Last resort: generate all from day topics only
        if len(selected_questions) == 0 and topics:
            llm_topics = topics[:2]  # Limit for rate limit
            selected_questions = MockTestService._generate_llm_questions_with_retry(
                topics=llm_topics, count=num_questions
            )

        logger.debug("Total questions: %s", len(selected_questions))
        logger.debug("====================")

        if not selected_questions:
            raise ValueError(f"No questions available. PYQs: {len(pyq_questions)}, LLM failed. Please add PYQs or try a different topic.")

        selected_questions = selected_questions[:num_questions]
        _SECURE_RNG.shuffle(selected_questions)  # NOSONAR

        topic = topics[0] if topics else None
        subject = topic.parent.name if topic and topic.parent else ""

        title = MockTestService._build_mock_test_title(subject, topic)

        with transaction.atomic():
            # Get topic name for description
            topic_name = main_topic.name if main_topic else "Mixed topics"

            mock_test = MockTest.objects.create(
                user=user,
                roadmap=roadmap,
                title=title,
                description=f"Day {day}: {topic_name}",
                duration_minutes=duration_minutes,
                status="active",
                generation_reason="daily_practice",
                generation_topics=topic_ids[:3],  # Only first 3 for relevant topics
                started_at=None,
            )

            total_marks = 0

            for q in selected_questions:
                mock_test.questions.add(q)
                total_marks += q.marks

            mock_test.total_marks = total_marks
            mock_test.question_count = len(selected_questions)
            mock_test.save()

            attempt = TestAttempt.objects.create(
                user=user, mock_test=mock_test, total_marks=mock_test.total_marks
            )

            return {"mock_test": mock_test, "attempt": attempt}

    @staticmethod
    def _build_mock_test_title(subject, topic):
        if subject and topic:
            return f"{subject} - {topic.name}"
        if topic:
            return topic.name
        return "Mock Test"

    @staticmethod
    def _get_pyq_questions(topics, count):
        if not topics:
            logger.warning("[PYQ] No topics provided")
            return []

        logger.debug("[PYQ] Searching for PYQs in %s topics", len(topics))

        subject_ids, topic_keywords = MockTestService._extract_subject_keywords(topics)
        all_pyqs = MockTestService._search_topic_matched_pyqs(topics, count)

        if len(all_pyqs) < count:
            all_pyqs = MockTestService._search_subject_keyword_pyqs(
                subject_ids, topic_keywords, count, all_pyqs
            )

        if len(all_pyqs) < count:
            all_pyqs = MockTestService._search_subject_fallback_pyqs(
                subject_ids, count, all_pyqs
            )

        return MockTestService._convert_pyqs_to_questions(all_pyqs[:count])

    @staticmethod
    def _extract_subject_keywords(topics):
        subject_ids = set()
        topic_keywords = set()
        for t in topics:
            if t.subject:
                subject_ids.add(t.subject.id)
            if t.name:
                keywords = t.name.lower().replace("-", " ").replace("_", " ").split()
                topic_keywords.update([k for k in keywords if len(k) > 3])
        logger.debug("[PYQ] Topic keywords: %s", list(topic_keywords)[:10])
        logger.debug("[PYQ] Subject IDs: %s", subject_ids)
        return subject_ids, topic_keywords

    @staticmethod
    def _search_topic_matched_pyqs(topics, count):
        topic_ids = [t.id for t in topics if t.id]
        if not topic_ids:
            return []
        pyqs = list(
            PYQ.objects.filter(topic_id__in=topic_ids, options__isnull=False).order_by(
                "?"
            )[: count * 2]
        )
        logger.debug("[PYQ] Topic-exact match: %s PYQs", len(pyqs))
        return list(pyqs)

    @staticmethod
    def _search_subject_keyword_pyqs(subject_ids, topic_keywords, count, existing_pyqs):
        if not subject_ids or not topic_keywords:
            return existing_pyqs

        keyword_query = Q()
        for kw in list(topic_keywords)[:10]:
            keyword_query |= Q(question_text__icontains=kw) | Q(
                topic__name__icontains=kw
            )
        pyqs = list(
            PYQ.objects.filter(
                keyword_query, topic__subject_id__in=subject_ids, options__isnull=False
            )
            .exclude(id__in=[p.id for p in existing_pyqs])
            .order_by("?")[:count]
        )
        logger.debug("[PYQ] Subject+keyword match: %s PYQs", len(pyqs))
        existing_pyqs.extend(pyqs)
        return existing_pyqs

    @staticmethod
    def _search_subject_fallback_pyqs(subject_ids, count, existing_pyqs):
        if not subject_ids:
            return existing_pyqs
        pyqs = list(
            PYQ.objects.filter(topic__subject_id__in=subject_ids, options__isnull=False)
            .exclude(id__in=[p.id for p in existing_pyqs])
            .order_by("?")[:count]
        )
        logger.debug("[PYQ] Subject fallback: %s PYQs", len(pyqs))
        existing_pyqs.extend(pyqs)
        return existing_pyqs

    @staticmethod
    def _get_question_bank_questions(topics, count, exclude_ids=None):
        topic_ids = [t.id for t in topics if t and t.id]
        if not topic_ids or count <= 0:
            return []

        queryset = Question.objects.filter(topic_id__in=topic_ids)

        if exclude_ids:
            queryset = queryset.exclude(id__in=exclude_ids)

        # Keep only answerable MCQ questions.
        usable = []
        for q in queryset.order_by("?"):
            options = MockTestService._normalize_options(q.options)
            correct = MockTestService._extract_correct_answer(q.correct_answer, options)
            if len(options) < 2 or not correct:
                continue
            if correct != q.correct_answer:
                q.correct_answer = correct
                q.options = options
                q.save(update_fields=["correct_answer", "options"])
            usable.append(q)
            if len(usable) >= count:
                break

        return usable

    @staticmethod
    def _convert_pyqs_to_questions(pyqs):
        questions = []
        for pyq in pyqs:
            options = MockTestService._normalize_options(pyq.options)
            if not options or len(options) < 2:
                logger.warning(
                    "[PYQ] Skipping PYQ %s - insufficient options: %s", pyq.id, options
                )
                continue
            correct_answer = MockTestService._extract_correct_answer(
                pyq.correct_answer, options
            )
            if not correct_answer:
                logger.warning(
                    "[PYQ] Skipping PYQ %s - invalid correct_answer: %s",
                    pyq.id,
                    pyq.correct_answer,
                )
                continue
            question = Question.objects.create(
                topic=pyq.topic,
                exam=pyq.exam,
                question_text=pyq.question_text,
                question_type=pyq.question_type or "mcq",
                options=options,
                correct_answer=correct_answer,
                explanation=pyq.explanation or "",
                difficulty="medium",
                marks=int(pyq.marks) if pyq.marks else 1,
                negative_marks=0.0,
                source="pyq",
                year=pyq.year,
            )
            questions.append(question)
        logger.info("[PYQ] Converted: %s questions", len(questions))
        return questions

    @staticmethod
    def _normalize_options(raw_options):
        payload = MockTestService._deserialize_options_payload(raw_options)
        if isinstance(payload, dict):
            return MockTestService._normalize_option_dict(payload)
        if isinstance(payload, list):
            return MockTestService._normalize_option_list(payload)
        return {}

    @staticmethod
    def _deserialize_options_payload(raw_options):
        if raw_options is None:
            return None
        if not isinstance(raw_options, str):
            return raw_options
        try:
            return json.loads(raw_options)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _normalize_option_dict(raw_options):
        normalized = {}
        for key, value in raw_options.items():
            key_str = str(key).strip().upper()
            if key_str:
                normalized[key_str] = str(value).strip()
        return normalized

    @staticmethod
    def _normalize_option_list(raw_options):
        normalized = {}
        for idx, value in enumerate(raw_options[: len(MockTestService._OPTION_KEYS)]):
            normalized[MockTestService._OPTION_KEYS[idx]] = str(value).strip()
        return normalized

    @staticmethod
    def _extract_correct_answer(correct, options=None):
        options_map = MockTestService._normalize_options(options)
        option_keys = set(options_map.keys())
        for candidate in MockTestService._collect_answer_candidates(correct):
            raw = str(candidate).strip()
            if not raw:
                continue
            cleaned = MockTestService._extract_option_letter(raw)
            if len(cleaned) == 1 and (not option_keys or cleaned in option_keys):
                return cleaned
            matched_key = MockTestService._find_option_key_by_value(raw, options_map)
            if matched_key:
                return matched_key

        return ""

    @staticmethod
    def _collect_answer_candidates(correct):
        if isinstance(correct, list):
            return [c for c in correct if c is not None]
        if isinstance(correct, dict):
            values = [c for c in correct.values() if c is not None]
            keys = [c for c in correct.keys() if c is not None]
            return values + keys
        return [correct] if correct is not None else []

    @staticmethod
    def _extract_option_letter(raw_value):
        cleaned = re.sub(
            r"^[\(\[\{]?\s*([A-Za-z])[\)\]\}\.\:\-]?\s*$", r"\1", raw_value
        )
        return cleaned.strip().upper()

    @staticmethod
    def _find_option_key_by_value(raw_value, options_map):
        lowered = raw_value.lower().strip()
        for key, value in options_map.items():
            if lowered == str(value).lower().strip():
                return key
        return ""

    @staticmethod
    def _normalize_text_answer(raw_value):
        return str(raw_value).upper().strip() if raw_value else ""

    @staticmethod
    def _resolve_answer_values(question, raw_user_answer):
        options = MockTestService._normalize_options(question.options)
        normalized_user_answer = MockTestService._extract_correct_answer(
            raw_user_answer, options
        ) or MockTestService._normalize_text_answer(raw_user_answer)
        normalized_correct_answer = MockTestService._extract_correct_answer(
            question.correct_answer, options
        ) or MockTestService._normalize_text_answer(question.correct_answer)
        is_correct = bool(normalized_user_answer) and (
            normalized_user_answer == normalized_correct_answer
        )
        return normalized_user_answer, normalized_correct_answer, is_correct

    @staticmethod
    def _get_any_pyq_fallback(count):
        any_with_answers = PYQ.objects.filter(
            correct_answer__isnull=False, options__isnull=False
        ).order_by("?")[:count]

        return MockTestService._convert_pyqs_to_questions(any_with_answers)

    @staticmethod
    def get_topic_stats(topics):
        """Get statistics about available PYQs for topics"""

        stats = {
            "topic_name": None,
            "pyq_available": 0,
            "subject": None,
            "subjects_with_pyq": [],
        }

        if not topics:
            return stats

        topic = topics[0]
        stats["topic_name"] = topic.name

        # Get PYQ count for topics
        pyq_count = PYQ.objects.filter(topic__in=topics).count()
        stats["pyq_available"] = pyq_count

        if topic.subject:
            stats["subject"] = topic.subject.name

            # Get all subjects with PYQs
            subjects_with_pyq = PYQ.objects.values_list(
                "topic__subject__name", flat=True
            ).distinct()
            stats["subjects_with_pyq"] = list(subjects_with_pyq)

        return stats

    @staticmethod
    def _generate_llm_questions(topics, count):
        client = Groq(api_key=settings.GROQ_API_KEY)
        main_topic = topics[0] if topics else None
        topic_name = main_topic.name if main_topic else "Agricultural Engineering"
        topic_names = [t.name for t in topics[:3]] if topics else [topic_name]

        prompt = MockTestService._build_llm_prompt(topic_name, count, topic_names)
        content = MockTestService._call_llm_api(client, prompt)
        return MockTestService._process_llm_response(content, topics)

    @staticmethod
    def _build_llm_prompt(topic_name, count, topic_names=None):
        constrained_topics = topic_names or [topic_name]
        topic_block = ", ".join(constrained_topics)
        return (
            "Generate exactly {count} high-quality GATE-level MCQ questions. "
            "Questions must be strictly relevant to these topics only: {topics}. "
            "Do not include any unrelated subject. "
            "Return ONLY a JSON array where each item has keys: "
            '"question", "options", "correct_answer", "explanation". '
            '"options" must be an object with keys A, B, C, D. '
            '"correct_answer" must be one of A, B, C, D.'
        ).format(count=count, topics=topic_block)

    @staticmethod
    def _call_llm_api(client, prompt):
        try:
            response = safe_llm_call(
                client,
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=5000,
            )
            content = response.choices[0].message.content
            logger.debug("[LLM] Response length: %s", len(content) if content else 0)
            return content if content else ""
        except (TimeoutError, ValueError, TypeError, AttributeError):
            logger.error("LLM question generation failed", exc_info=True)
            raise

    @staticmethod
    def _process_llm_response(content, topics):
        if not content:
            return []

        content = content.strip()

        # Handle markdown and find JSON array
        content = MockTestService._clean_markdown(content)
        start = content.find('[')
        if start == -1:
            return []

        content = MockTestService._extract_json_array(content, start)

        # Parse JSON
        questions_data = MockTestService._parse_json_content(content)
        if not questions_data:
            return []

        return MockTestService._create_questions_from_parsed(questions_data, topics)

    @staticmethod
    def _clean_markdown(content):
        """Clean markdown code blocks from content."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        if content.startswith('```'):
            content = re.sub(r'^```\w*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        return content.strip()

    @staticmethod
    def _extract_json_array(content, start):
        """Extract the JSON array by finding matching brackets."""
        depth = 0
        for i, c in enumerate(content[start:], start):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return content[start:i+1]
        return content[start:]

    @staticmethod
    def _parse_json_content(content):
        """Parse JSON content, handling common issues."""
        content = content.replace('}{', '},{').replace('\n', '').replace('  ', '')
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = MockTestService._extract_json_objects(content)

        if not isinstance(data, list):
            return []
        logger.debug("[LLM] Parsed %s questions", len(data))
        return data

    @staticmethod
    def _create_questions_from_parsed(questions_data, topics):
        """Create Question objects from parsed data."""
        created_questions = []
        for idx, q_data in enumerate(questions_data):
            question = MockTestService._create_single_question(q_data, topics, idx, len(questions_data))
            if question:
                created_questions.append(question)
        return created_questions

    @staticmethod
    def _create_single_question(q_data, topics, idx, total):
        """Create a single question from data."""
        try:
            opts = MockTestService._normalize_options(q_data.get("options", {}))
            if not opts or len(opts) < 2:
                logger.warning("Skipping generated question - insufficient options: %s", opts)
                return None

            correct_answer = MockTestService._extract_correct_answer(
                q_data.get("correct_answer", "") or q_data.get("answer", ""),
                opts,
            )
            if not correct_answer:
                logger.warning(
                    "Skipping generated question - invalid correct_answer: %s",
                    q_data.get("correct_answer", ""),
                )
                return None

            logger.debug(
                "[LLM] Creating question %s/%s: %s...",
                idx + 1,
                total,
                q_data.get("question", "")[:50],
            )

            return Question.objects.create(
                topic=topics[0] if topics else None,
                question_text=q_data.get("question", ""),
                question_type="mcq",
                options=opts,
                correct_answer=correct_answer,
                explanation=q_data.get("explanation", ""),
                difficulty="medium",
                marks=1,
                negative_marks=0.0,
                source="llm",
            )
        except (TypeError, ValueError, KeyError):
            logger.warning("Skipping invalid generated question payload", exc_info=True)
            return None

    @staticmethod
    def _generate_llm_questions_with_retry(topics, count, max_retries=2):
        for _ in range(max_retries):
            try:
                questions = MockTestService._generate_llm_questions(topics, count)
            except (TimeoutError, ValueError, TypeError, AttributeError):
                logger.error("Retry attempt for LLM question generation failed", exc_info=True)
                continue
            if questions:
                return questions
        return []

    @staticmethod
    def _extract_json_objects(content):
        """Extract valid question objects from JSON content using regex."""
        questions_list = []

        # Try regex extraction
        pattern = r'\{(?:[^{}]|\{[^{}]*\})*\}'
        for match in re.finditer(pattern, content):
            try:
                obj = json.loads(match.group())
                if "question" in obj and "options" in obj:
                    questions_list.append(obj)
            except (json.JSONDecodeError, OSError):
                continue

        if not questions_list:
            logger.warning("[LLM] No valid question objects found via regex")
        return questions_list

    @staticmethod
    def submit_answer(user, attempt_id, question_id, user_answer, time_taken_seconds=0):
        """Submit a single answer during test"""
        logger.debug("=== SUBMIT ANSWER DEBUG ===")
        logger.debug(
            "user: %s, attempt_id: %s, question_id: %s", user, attempt_id, question_id
        )
        logger.debug("user_answer: %s", user_answer)

        try:
            attempt = TestAttempt.objects.get(id=attempt_id, user=user)
            logger.debug("Attempt found: %s", attempt.id)
        except TestAttempt.DoesNotExist:
            logger.warning("TestAttempt not found for attempt_id=%s and user_id=%s", attempt_id, getattr(user, "id", None))
            return None, None

        try:
            question = Question.objects.get(id=question_id)
            logger.debug(
                "Question found: %s, correct_answer: %s",
                question.id,
                question.correct_answer,
            )
        except Question.DoesNotExist:
            logger.warning("Question not found for question_id=%s", question_id)
            return None, attempt

        normalized_user_answer, _, is_correct = MockTestService._resolve_answer_values(
            question, user_answer
        )

        logger.debug("is_correct: %s", is_correct)

        answer, created = Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "user_answer": normalized_user_answer,
                "is_correct": is_correct,
                "marks_obtained": question.marks if is_correct else 0,
                "time_taken_seconds": time_taken_seconds,
            },
        )

        logger.info("Answer saved: %s, created: %s", answer.id, created)
        logger.debug("===========================")

        return answer, attempt

    @staticmethod
    def finalize_test(attempt_id):
        """Finalize test and calculate results"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
        except TestAttempt.DoesNotExist:
            return None

        # Calculate total marks and counts across ALL test questions
        questions = attempt.mock_test.questions.all()
        answers_by_question_id = {a.question_id: a for a in attempt.answers.all()}

        total_marks = 0
        obtained_marks = 0
        correct = 0
        incorrect = 0
        unanswered = 0

        for question in questions:
            total_marks += question.marks
            answer = answers_by_question_id.get(question.id)
            if not answer or not (answer.user_answer or "").strip():
                unanswered += 1
                continue

            obtained_marks += answer.marks_obtained

            if answer.is_correct:
                correct += 1
            else:
                incorrect += 1

        attempt.score = obtained_marks
        attempt.total_marks = total_marks
        attempt.percentage = round(
            (obtained_marks / total_marks * 100) if total_marks > 0 else 0, 2
        )
        attempt.correct_answers = correct
        attempt.incorrect_answers = incorrect
        attempt.unanswered = unanswered
        attempt.submitted_at = timezone.now()
        attempt.save()

        return attempt

    @staticmethod
    def evaluate_test(attempt_id, answers):
        """Evaluate a test attempt"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
        except TestAttempt.DoesNotExist:
            return {"error": "Attempt not found"}

        correct = 0
        wrong = 0
        unanswered = 0
        total_marks = 0
        obtained_marks = 0
        detailed_results = []

        for answer in answers:
            evaluated = MockTestService._evaluate_single_answer(attempt, answer)
            if not evaluated:
                continue

            question = evaluated["question"]
            total_marks += question.marks
            obtained_marks += evaluated["obtained_marks"]

            if evaluated["status"] == "correct":
                correct += 1
            elif evaluated["status"] == "wrong":
                wrong += 1
            else:
                unanswered += 1

            detailed_results.append(
                {
                    "question_id": question.id,
                    "user_answer": evaluated["user_answer"],
                    "correct_answer": evaluated["correct_answer"],
                    "is_correct": evaluated["is_correct"],
                    "marks": question.marks,
                    "explanation": question.explanation,
                }
            )

        attempt.score = obtained_marks
        attempt.completed_at = timezone.now()
        attempt.save()

        return {
            "attempt_id": attempt_id,
            "total_questions": correct + wrong + unanswered,
            "correct": correct,
            "wrong": wrong,
            "unanswered": unanswered,
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "percentage": round(
                (obtained_marks / total_marks * 100) if total_marks > 0 else 0, 2
            ),
            "results": detailed_results,
        }

    @staticmethod
    def _evaluate_single_answer(attempt, answer_payload):
        question_id = answer_payload.get("question_id")
        raw_user_answer = answer_payload.get("answer", "")

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return None

        normalized_user_answer, normalized_correct_answer, is_correct = (
            MockTestService._resolve_answer_values(question, raw_user_answer)
        )
        marks_obtained = question.marks if is_correct else 0

        Answer.objects.create(
            attempt=attempt,
            question=question,
            user_answer=normalized_user_answer,
            is_correct=is_correct,
            marks_obtained=marks_obtained,
        )

        if is_correct:
            status = "correct"
        elif raw_user_answer:
            status = "wrong"
        else:
            status = "unanswered"

        return {
            "question": question,
            "user_answer": normalized_user_answer,
            "correct_answer": normalized_correct_answer,
            "is_correct": is_correct,
            "obtained_marks": marks_obtained,
            "status": status,
        }
