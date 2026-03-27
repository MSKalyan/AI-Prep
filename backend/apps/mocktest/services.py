import json
import random
import re
from django.utils import timezone
from django.db import transaction
from .models import Question, MockTest, TestAttempt, Answer
from groq import Groq
from django.conf import settings


class MockTestService:

    @staticmethod
    def create_mock_test(user, roadmap, day, topics, num_questions=10, duration_minutes=30):

        # ✅ FIND EXISTING TEST PROPERLY
        existing_tests = MockTest.objects.filter(
            user=user,
            roadmap=roadmap,
            status="active",
            generation_reason="daily_practice"
        )

        existing_test = None

        for t in existing_tests:
            if day in (t.generation_topics or []):
                existing_test = t
                break
        if existing_test:
            attempt = TestAttempt.objects.filter(
                user=user,
                mock_test=existing_test,
                submitted_at__isnull=True
            ).first()

            # ✅ FIX: Reset timer when reusing test
            if existing_test.started_at:
                existing_test.started_at = None
                existing_test.save(update_fields=["started_at"])

            if not attempt:
                attempt = TestAttempt.objects.create(
                    user=user,
                    mock_test=existing_test,
                    total_marks=existing_test.total_marks
                )

            return {
                "mock_test": existing_test,
                "attempt": attempt
            }
        # ✅ STEP 2: Fetch PYQs
        pyq_questions = list(
            Question.objects.filter(topic__in=topics, source='pyq')
        )

        selected_questions = random.sample(
            pyq_questions,
            min(len(pyq_questions), num_questions)
        )

        remaining = num_questions - len(selected_questions)

        # ✅ STEP 3: LLM fallback (strong)
        if remaining > 0:
            llm_questions = MockTestService._generate_llm_questions(
                topics=topics,
                count=remaining
            )
            selected_questions.extend(llm_questions)

        # ✅ EXTRA FALLBACK (IMPORTANT)
        if not selected_questions:
            print("⚠️ No PYQs + LLM failed → retrying full LLM generation")

            selected_questions = MockTestService._generate_llm_questions(
                topics=topics,
                count=num_questions
            )

        # ✅ FINAL SAFETY
        if not selected_questions:
            raise ValueError("No questions available even after LLM fallback")

        selected_questions = selected_questions[:num_questions]

        if not selected_questions:
            raise ValueError("No questions available")

        random.shuffle(selected_questions)

        # ✅ STEP 4: Create test
        with transaction.atomic():

            mock_test = MockTest.objects.create(
                user=user,
                roadmap=roadmap,
                title=f"Day {day} Practice Test",
                description=f"Day {day} mixed topics test",
                duration_minutes=duration_minutes,
                status="active",
                generation_reason="daily_practice",
                generation_topics=[day],
                started_at=None
            )

            total_marks = 0

            for q in selected_questions:
                mock_test.questions.add(q)
                total_marks += q.marks

            mock_test.total_marks = total_marks
            mock_test.question_count = len(selected_questions)
            mock_test.save()

            attempt = TestAttempt.objects.create(
                user=user,
                mock_test=mock_test,
                total_marks=mock_test.total_marks
            )

            return {
                "mock_test": mock_test,
                "attempt": attempt
            }

    @staticmethod
    def _generate_llm_questions(topics, count):
        client = Groq(api_key=settings.GROQ_API_KEY)

        topic_names = [t.name for t in topics]

        sample_pyqs = Question.objects.filter(
            topic__in=topics,
            source='pyq'
        )[:5]

        context = "\n".join([q.question_text for q in sample_pyqs])

        prompt = f"""
Generate {count} GATE-level MCQs.

Topics: {", ".join(topic_names)}

Rules:
- Return ONLY valid JSON array
- Each item must have:
  question_text, options, correct_answer, explanation
- options must be dictionary with keys A, B, C, D
- NO markdown
- NO extra text

Example:
[
  {{
    "question_text": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A",
    "explanation": "..."
  }}
]

"""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()
            content = re.sub(r"```json|```", "", content).strip()

            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                content = match.group(0)

            data = json.loads(content)

            questions = []

            for q in data[:count]:
                question = Question.objects.create(
                    question_text=q["question_text"],
                    options=q["options"],
                    correct_answer=q["correct_answer"],
                    explanation=q.get("explanation", ""),
                    marks=1,
                    negative_marks=0,
                    source="llm",
                    topic=random.choice(topics)
                )
                questions.append(question)

            return questions

        except Exception as e:
            print("LLM FAILED:", e)
            return []

    @staticmethod
    def start_test_attempt(user, mock_test_id):
        try:
            mock_test = MockTest.objects.get(id=mock_test_id)

            attempt = TestAttempt.objects.create(
                user=user,
                mock_test=mock_test,
                total_marks=mock_test.total_marks
            )

            return attempt

        except MockTest.DoesNotExist:
            return None

    @staticmethod
    def submit_answer(user, attempt_id, question_id, user_answer, time_taken_seconds=None):

        try:
            attempt = TestAttempt.objects.get(id=attempt_id, user=user)
            question = Question.objects.get(id=question_id)

            # ✅ STEP 1: Time validation FIRST
            if attempt.mock_test.started_at:
                elapsed = (timezone.now() - attempt.mock_test.started_at).total_seconds()
                if elapsed > attempt.mock_test.duration_minutes * 60:
                    raise Exception("Time is up")

            is_correct = (user_answer == question.correct_answer)

            # ✅ STEP 2: Normalize time
            time_taken_seconds = time_taken_seconds or 0

            # ✅ STEP 3: Get previous answer BEFORE update
            previous_answer = Answer.objects.filter(
                attempt=attempt,
                question=question
            ).first()

            prev_correct = previous_answer.is_correct if previous_answer else None

            # ✅ STEP 4: Handle time accumulation (CRITICAL FIX)
            if previous_answer:
                accumulated_time = previous_answer.time_taken_seconds + time_taken_seconds
            else:
                accumulated_time = time_taken_seconds

            # ✅ STEP 5: Update/create (same structure, minimal change)
            answer, created = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "user_answer": user_answer,
                    "is_correct": is_correct,
                    "time_taken_seconds": accumulated_time,
                },
            )

            # ✅ STEP 6: Adjust previous score (unchanged)
            if prev_correct is not None:
                if prev_correct:
                    attempt.score -= question.marks
                else:
                    attempt.score += question.negative_marks

            # ✅ STEP 7: Apply new score (unchanged)
            if is_correct:
                attempt.score += question.marks
                answer.marks_obtained = question.marks
            else:
                attempt.score -= question.negative_marks
                answer.marks_obtained = -question.negative_marks

            # ✅ STEP 8: Save (unchanged)
            attempt.save()
            answer.save(update_fields=["marks_obtained"])

            return answer, attempt

        except TestAttempt.DoesNotExist:
            raise Exception("Invalid attempt")

        except Question.DoesNotExist:
            raise Exception("Invalid question")
    @staticmethod
    def finalize_test(attempt_id):
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)

            # ✅ Prevent double submission
            if attempt.submitted_at:
                return attempt

            attempt.submitted_at = timezone.now()

            # ✅ Calculate stats
            answers = attempt.answers.all()
            total_questions = attempt.mock_test.questions.count()

            correct = answers.filter(is_correct=True).count()
            incorrect = answers.filter(is_correct=False).count()
            answered = answers.count()
            unanswered = total_questions - answered

            # ✅ Time taken
            if attempt.mock_test.started_at:
                elapsed = (attempt.submitted_at - attempt.mock_test.started_at).total_seconds()
                attempt.time_taken_minutes = round(elapsed / 60, 2)

            # ✅ Percentage
            if attempt.total_marks > 0:
                attempt.percentage = (attempt.score / attempt.total_marks) * 100
            else:
                attempt.percentage = 0

            # ✅ Save stats
            attempt.correct_answers = correct
            attempt.incorrect_answers = incorrect
            attempt.unanswered = unanswered

            attempt.save()

            return attempt

        except TestAttempt.DoesNotExist:
            return None
