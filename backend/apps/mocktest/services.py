import json
import random
import re
import os
from django.utils import timezone
from django.db import transaction

from .models import Question, MockTest, TestAttempt, Answer
from apps.roadmap.models import PYQ, Topic
from groq import Groq
from django.conf import settings


class MockTestService:
    @staticmethod
    def create_mock_test(
        user, roadmap, day, topics, num_questions=10, duration_minutes=30
    ):
        topic_ids = sorted([t.id for t in topics])

        print("\n=== MOCKTEST DEBUG ===")
        print(f"Topics: {[t.name for t in topics]}")
        print(f"Num questions requested: {num_questions}")

        # PRIMARY SOURCE: Get PYQs from roadmap.PYQ table
        pyq_questions = MockTestService._get_pyq_questions(topics, num_questions)

        print(f"PYQ questions found: {len(pyq_questions)}")

        selected_questions = pyq_questions[:]

        remaining = num_questions - len(selected_questions)

        # FALLBACK: Use LLM to generate questions if not enough PYQs
        llm_questions = []
        if remaining > 0:
            print(f"Generating {remaining} questions via LLM fallback")
            llm_questions = MockTestService._generate_llm_questions_with_retry(
                topics=topics, count=remaining
            )
            print(f"LLM questions generated: {len(llm_questions)}")
            selected_questions.extend(llm_questions)

        # Last resort: generate all questions with LLM
        if len(selected_questions) == 0:
            print("No questions found, generating all via LLM")
            selected_questions = MockTestService._generate_llm_questions_with_retry(
                topics=topics, count=num_questions
            )

        print(f"Total questions: {len(selected_questions)}")
        print("====================\n")

        selected_questions = selected_questions[:num_questions]
        random.shuffle(selected_questions)

        topic = topics[0] if topics else None
        subject = topic.parent.name if topic and topic.parent else ""

        title = MockTestService._build_mock_test_title(subject, topic)

        with transaction.atomic():
            mock_test = MockTest.objects.create(
                user=user,
                roadmap=roadmap,
                title=title,
                description=f"Day {day} mixed topics test",
                duration_minutes=duration_minutes,
                status="active",
                generation_reason="daily_practice",
                generation_topics=topic_ids,
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

        topic_names = [t.name for t in topics]

        prompt = f"""Generate {count} GATE-level MCQs for: {", ".join(topic_names[:5])}.

OUTPUT: Start with [ and end with ]. NO other text.
Format: [{{"question": "...", "options": {{"A":"...","B":"...","C":"...","D":"..."}}, "correct_answer": "A", "explanation": "..."}}]"""

        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
            )

            content = response.choices[0].message.content

            print(f"  [LLM] Response length: {len(content) if content else 0}")

            if not content:
                print("  [LLM] Empty response from LLM")
                return []

            # Extract JSON
            content = content.strip()

            # Handle markdown code fences
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            # Also handle plain text with JSON (like "Here are 10 questions:\n[...")
            # Find the first '[' and parse from there
            bracket_pos = content.find("[")
            if bracket_pos >= 0:
                content = content[bracket_pos:]

            # Also handle any leading text before [
            if not content.startswith("["):
                import re

                match = re.search(r"\[", content)
                if match:
                    content = content[match.start() :]

            print(f"  [LLM] Content to parse: {content[:200]}...")

            questions_data = json.loads(content)

            created_questions = []
            for q_data in questions_data:
                print(
                    f"  [LLM] Creating question: {q_data.get('question', '')[:50]}..."
                )
                question = Question.objects.create(
                    topic=topics[0] if topics else None,
                    question_text=q_data.get("question", ""),
                    question_type="mcq",
                    options=q_data.get("options", {}),
                    correct_answer=q_data.get("correct_answer", "").upper(),
                    explanation=q_data.get("explanation", ""),
                    difficulty="medium",
                    marks=1,
                    negative_marks=0.0,
                    source="llm",
                )
                created_questions.append(question)

            return created_questions

        except Exception as e:
            print(f"LLM question generation error: {e}")
            return []

    @staticmethod
    def _generate_llm_questions_with_retry(topics, count, max_retries=2):
        for _ in range(max_retries):
            questions = MockTestService._generate_llm_questions(topics, count)
            if questions:
                return questions
        return []

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
