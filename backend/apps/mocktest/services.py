import json
import re
import os
import secrets
from django.utils import timezone
from django.db import transaction

from .models import Question, MockTest, TestAttempt, Answer
from apps.roadmap.models import PYQ, Topic
from groq import Groq
from django.conf import settings

_SECURE_RNG = secrets.SystemRandom()


class MockTestService:
    @staticmethod
    def create_mock_test(
        user, roadmap, day, topics, num_questions=10, duration_minutes=30
    ):
        topic_ids = sorted([t.id for t in topics])

        print("\n=== MOCKTEST DEBUG ===")
        print(f"Day: {day}")
        print(f"Topics: {[t.name for t in topics]}")
        print(f"Num questions requested: {num_questions}")

        # PRIMARY SOURCE: Get PYQs from roadmap.PYQ table - search ALL day topics
        main_topic = topics[0] if topics else None
        pyq_questions = MockTestService._get_pyq_questions(topics, num_questions) if topics else []

        print(f"PYQ questions found in {len(topics)} day topics: {len(pyq_questions)}")

        selected_questions = list(pyq_questions)  # Copy list
        remaining = num_questions - len(selected_questions)

        # FALLBACK: Use LLM to generate for remaining count, focusing on day topics
        llm_questions = []
        if remaining > 0:
            # Use day topics for LLM to keep relevance
            llm_topics = topics if len(topics) <= 3 else topics[:3]
            print(f"Generating {remaining} questions via LLM for day topics: {[t.name for t in llm_topics]}")
            llm_questions = MockTestService._generate_llm_questions_with_retry(
                topics=llm_topics, count=remaining
            )
            print(f"LLM questions generated: {len(llm_questions)}")
            selected_questions.extend(llm_questions)

        # Last resort: generate all from day topics only
        if len(selected_questions) == 0 and topics:
            llm_topics = topics[:2]  # Limit for rate limit
            selected_questions = MockTestService._generate_llm_questions_with_retry(
                topics=llm_topics, count=num_questions
            )

        print(f"Total questions: {len(selected_questions)}")
        print("====================\n")

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
            print("  [PYQ] No topics provided")
            return []

        print(f"  [PYQ] Searching for PYQs in {len(topics)} topics")

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
        print(f"  [PYQ] Topic keywords: {list(topic_keywords)[:10]}")
        print(f"  [PYQ] Subject IDs: {subject_ids}")
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
        print(f"  [PYQ] Topic-exact match: {len(pyqs)} PYQs")
        return list(pyqs)

    @staticmethod
    def _search_subject_keyword_pyqs(subject_ids, topic_keywords, count, existing_pyqs):
        if not subject_ids or not topic_keywords:
            return existing_pyqs
        from django.db.models import Q

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
        print(f"  [PYQ] Subject+keyword match: {len(pyqs)} PYQs")
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
        print(f"  [PYQ] Subject fallback: {len(pyqs)} PYQs")
        existing_pyqs.extend(pyqs)
        return existing_pyqs

    @staticmethod
    def _convert_pyqs_to_questions(pyqs):
        questions = []
        for pyq in pyqs:
            options = pyq.options if isinstance(pyq.options, dict) else {}
            if not options or len(options) < 2:
                print(f"  [PYQ] Skipping PYQ {pyq.id} - insufficient options: {options}")
                continue
            correct_answer = MockTestService._extract_correct_answer(pyq.correct_answer)
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
        print(f"  [PYQ] Converted: {len(questions)} questions")
        return questions

    @staticmethod
    def _extract_correct_answer(correct):
        if not correct:
            return "A"
        if isinstance(correct, list) and correct:
            return correct[0]
        if isinstance(correct, str):
            return correct.upper() if len(correct) == 1 else "A"
        return "A"

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

        prompt = MockTestService._build_llm_prompt(topic_name, count)
        content = MockTestService._call_llm_api(client, prompt)
        return MockTestService._process_llm_response(content, topics)

    @staticmethod
    def _build_llm_prompt(topic_name, count):
        return "Generate {} GATE-level MCQs specifically on \"{}\" topic. Output: JSON array only.".format(count, topic_name)

    @staticmethod
    def _call_llm_api(client, prompt):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=5000,
            )
            content = response.choices[0].message.content
            print("  [LLM] Response length: {}".format(len(content) if content else 0))
            return content if content else ""
        except Exception as e:
            print("LLM question generation error: {}".format(e))
            return ""

    @staticmethod
    def _process_llm_response(content, topics):
        if not content:
            return []

        import re
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
        import re
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
        print("  [LLM] Parsed {} questions".format(len(data)))
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
            opts = q_data.get("options", {})
            if not opts or len(opts) < 2:
                print("    Skipping - insufficient options: {}".format(opts))
                return None

            print("  [LLM] Creating question {}/{}: {}...".format(
                idx+1, total, q_data.get("question", "")[:50]))

            return Question.objects.create(
                topic=topics[0] if topics else None,
                question_text=q_data.get("question", ""),
                question_type="mcq",
                options=opts,
                correct_answer=q_data.get("correct_answer", "").upper(),
                explanation=q_data.get("explanation", ""),
                difficulty="medium",
                marks=1,
                negative_marks=0.0,
                source="llm",
            )
        except Exception as e:
            print("    Error creating question: {}".format(e))
            return None

    @staticmethod
    def _generate_llm_questions_with_retry(topics, count, max_retries=2):
        for _ in range(max_retries):
            questions = MockTestService._generate_llm_questions(topics, count)
            if questions:
                return questions
        return []

    @staticmethod
    def _extract_json_objects(content):
        """Extract valid question objects from JSON content using regex."""
        import re
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
            print("  [LLM] No valid question objects found via regex")
        return questions_list

    @staticmethod
    def submit_answer(user, attempt_id, question_id, user_answer, time_taken_seconds=0):
        """Submit a single answer during test"""
        print("\n=== SUBMIT ANSWER DEBUG ===")
        print(f"user: {user}, attempt_id: {attempt_id}, question_id: {question_id}")
        print(f"user_answer: {user_answer}")

        try:
            attempt = TestAttempt.objects.get(id=attempt_id, user=user)
            print(f"Attempt found: {attempt.id}")
        except TestAttempt.DoesNotExist:
            print("Attempt not found!")
            return None, None

        try:
            question = Question.objects.get(id=question_id)
            print(
                f"Question found: {question.id}, correct_answer: {question.correct_answer}"
            )
        except Question.DoesNotExist:
            print("Question not found!")
            return None, attempt

        user_answer = user_answer.upper() if user_answer else ""

        is_correct = (
            user_answer == question.correct_answer.upper()
            if question.correct_answer
            else False
        )

        print(f"is_correct: {is_correct}")

        answer, created = Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "user_answer": user_answer,
                "is_correct": is_correct,
                "marks_obtained": question.marks if is_correct else 0,
                "time_taken_seconds": time_taken_seconds,
            },
        )

        print(f"Answer saved: {answer.id}, created: {created}")
        print("===========================\n")

        return answer, attempt

    @staticmethod
    def finalize_test(attempt_id):
        """Finalize test and calculate results"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
        except TestAttempt.DoesNotExist:
            return None

        # Calculate total marks and counts
        total_marks = 0
        obtained_marks = 0
        correct = 0
        incorrect = 0
        unanswered = 0

        for answer in attempt.answers.all():
            question = answer.question
            total_marks += question.marks
            obtained_marks += answer.marks_obtained

            if answer.user_answer:
                if answer.is_correct:
                    correct += 1
                else:
                    incorrect += 1
            else:
                unanswered += 1

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
            question_id = answer.get("question_id")
            user_answer = answer.get("answer", "").upper()

            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                continue

            is_correct = user_answer == question.correct_answer.upper()

            Answer.objects.create(
                attempt=attempt,
                question=question,
                user_answer=user_answer,
                is_correct=is_correct,
                marks_obtained=question.marks if is_correct else 0,
            )

            if is_correct:
                correct += 1
                obtained_marks += question.marks
            elif user_answer:
                wrong += 1
            else:
                unanswered += 1

            total_marks += question.marks

            detailed_results.append(
                {
                    "question_id": question_id,
                    "user_answer": user_answer,
                    "correct_answer": question.correct_answer,
                    "is_correct": is_correct,
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
