import json
import random
import re
from django.utils import timezone
from django.db import transaction
from sympy import content
from .models import Question, MockTest, TestAttempt, Answer
from groq import Groq
from django.conf import settings


class MockTestService:

    @staticmethod
    def create_mock_test(user, roadmap, day, topics, num_questions=10, duration_minutes=30):

        topic_ids = sorted([t.id for t in topics])

        existing_test = MockTest.objects.filter(
            user=user,
            roadmap=roadmap,
            status="active",
            generation_reason="daily_practice",
            generation_topics=topic_ids  # exact match
        ).first()

        if existing_test:
            attempt = TestAttempt.objects.filter(
                user=user,
                mock_test=existing_test,
                submitted_at__isnull=True
            ).first()

            
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

        pyq_questions = list(
            Question.objects.filter(
                topic__in=topics,
                source='pyq'
            ).order_by('?')[:num_questions]
        )

        selected_questions = pyq_questions[:]  # no random.sample

        remaining = num_questions - len(selected_questions)

        if remaining > 0:
            llm_questions = MockTestService._generate_llm_questions(
                topics=topics,
                count=remaining
            )
            selected_questions.extend(llm_questions)

        if not selected_questions:
            fallback_questions = list(
                Question.objects.filter(source='pyq')
                .order_by('?')[:num_questions]
            )

            if fallback_questions:
                selected_questions = fallback_questions
            else:
                raise ValueError("No questions available in system")
        selected_questions = selected_questions[:num_questions]

        if len(selected_questions) < num_questions:
            selected_ids = [q.id for q in selected_questions]

            if len(selected_questions) < num_questions:
                needed = num_questions - len(selected_questions)

                fallback = list(
                    Question.objects.filter(topic__in=topics)
                    .exclude(id__in=selected_ids)
                    .order_by('?')[:needed]
                )

                selected_questions.extend(fallback)
                selected_ids.extend([q.id for q in fallback])

            if len(selected_questions) < num_questions:
                needed = num_questions - len(selected_questions)

                fallback = list(
                    Question.objects.filter(source='pyq')
                    .exclude(id__in=selected_ids)
                    .order_by('?')[:needed]
                )

                selected_questions.extend(fallback)
                selected_ids.extend([q.id for q in fallback])


            if len(selected_questions) < num_questions:
                needed = num_questions - len(selected_questions)

                fallback = list(
                    Question.objects.exclude(id__in=selected_ids)
                    .order_by('?')[:needed]
                )

                selected_questions.extend(fallback)
        if not selected_questions:
            raise ValueError("No questions exist in database")
        random.shuffle(selected_questions)
        topic = topics[0]  # however you're selecting

        subject = topic.parent.name if topic.parent else ""

        title = f"{subject} - {topic.name}" if subject else topic.name
        with transaction.atomic():

            mock_test = MockTest.objects.create(
                user=user,
                roadmap=roadmap,
                title=title,
                description=f"Day {day} mixed topics test",
                duration_minutes=duration_minutes,
                status="active",
                generation_reason="daily_practice",
                generation_topics=topic_ids,  # ✅ FIXED
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
    Use these reference questions to understand topic style:
    {context}

    Topics: {", ".join(topic_names)}

    Generate {count} HIGH-QUALITY GATE-level MCQs.

    STRICT RULES:
    - Questions MUST be strictly from these topics
    - Each question MUST be factually correct
    - correct_answer must be EXACTLY one of A/B/C/D
    - options must be meaningful and non-overlapping
    - explanation must justify the correct answer
    - DO NOT generate if unsure
    - Keep each question short (max 2 lines)
    - Keep explanation under 3 lines

    Return ONLY JSON:

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
                temperature=0.2,  
                max_tokens=1200
            )

            content = response.choices[0].message.content.strip()

            content = re.sub(r"```json|```", "", content).strip()

            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                content = match.group(0)
        

            def extract_json_array(text):
                try:
                    match = re.search(r"\[.*\]", text, re.DOTALL)
                    if not match:
                        return []

                    json_str = match.group(0)

                    # 🔥 FIX common LLM issues
                    json_str = json_str.replace("\n", " ")
                    json_str = re.sub(r",\s*}", "}", json_str)   # trailing commas
                    json_str = re.sub(r",\s*]", "]", json_str)

                    return json.loads(json_str)

                except Exception:
                    return []
            data = extract_json_array(content)
            questions = []


            def validate_question(q):
                required_fields = ["question_text", "options", "correct_answer"]
                if not all(field in q for field in required_fields):
                    return False

                if not isinstance(q["options"], dict):
                    return False

                if set(q["options"].keys()) != {"A", "B", "C", "D"}:
                    return False

                if q["correct_answer"] not in q["options"]:
                    return False

                if len(q["question_text"].strip()) < 10:
                    return False

                correct_text = q["options"][q["correct_answer"]]
                if not correct_text or len(correct_text.strip()) < 2:
                    return False

                return True

            def is_topic_relevant(question_text, topics):
                topic_keywords = [t.name.lower() for t in topics]
                q_lower = question_text.lower()

                return any(keyword in q_lower for keyword in topic_keywords)


            for q in data:
                if len(questions) >= count:
                    break

                if not validate_question(q):
                    continue

                if not is_topic_relevant(q["question_text"], topics):
                    continue

                correct_answer = q["correct_answer"].strip().upper()

                options = {
                    key.strip().upper(): value.strip()
                    for key, value in q["options"].items()
                }

                if correct_answer not in options:
                    continue

                question = Question.objects.create(
                    question_text=q["question_text"].strip(),
                    options=options,
                    correct_answer=correct_answer,
                    explanation=q.get("explanation", "").strip(),
                    marks=1,
                    negative_marks=0,
                    source="llm",
                    topic=random.choice(topics)  # acceptable fallback
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

            if attempt.mock_test.started_at:
                elapsed = (timezone.now() - attempt.mock_test.started_at).total_seconds()
                if elapsed > attempt.mock_test.duration_minutes * 60:
                    raise Exception("Time is up")

            def normalize_answer(user_answer, question):
                if not user_answer:
                    return None

                user_answer = user_answer.strip()

                if user_answer in question.options:
                    return user_answer

                for key, value in question.options.items():
                    if user_answer.lower() == value.lower():
                        return key

                return None


            normalized = normalize_answer(user_answer, question)
            if normalized is None:
                raise Exception("Invalid answer format")
            is_correct = (normalized == question.correct_answer)
            time_taken_seconds = time_taken_seconds or 0

            previous_answer = Answer.objects.filter(
                attempt=attempt,
                question=question
            ).first()

            prev_correct = previous_answer.is_correct if previous_answer else None

            if previous_answer:
                accumulated_time = previous_answer.time_taken_seconds + time_taken_seconds
            else:
                accumulated_time = time_taken_seconds

            answer, created = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "user_answer": normalized,
                    "is_correct": is_correct,
                    "time_taken_seconds": accumulated_time,
                },
            )

            if prev_correct is not None:
                if prev_correct:
                    attempt.score -= question.marks
                else:
                    attempt.score += question.negative_marks

            if is_correct:
                delta = question.marks
            else:
                delta = -abs(question.negative_marks)

            attempt.score += delta
            answer.marks_obtained = delta
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

            if attempt.submitted_at:
                return attempt

            attempt.submitted_at = timezone.now()

            answers = attempt.answers.all()
            total_questions = attempt.mock_test.questions.count()

            correct = answers.filter(is_correct=True).count()
            incorrect = answers.filter(is_correct=False).count()
            answered = answers.count()
            unanswered = total_questions - answered

            if attempt.mock_test.started_at:
                elapsed = (attempt.submitted_at - attempt.mock_test.started_at).total_seconds()
                attempt.time_taken_minutes = round(elapsed / 60, 2)

            if attempt.total_marks > 0:
                attempt.percentage = (attempt.score / attempt.total_marks) * 100
            else:
                attempt.percentage = 0

            attempt.correct_answers = correct
            attempt.incorrect_answers = incorrect
            attempt.unanswered = unanswered

            attempt.save()

            return attempt

        except TestAttempt.DoesNotExist:
            return None
