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
    def create_mock_test(user, topic, num_questions=5, duration_minutes=60):
        """Create mock test using PYQ + LLM fallback"""

        # 🔹 Fetch PYQs
        pyq_questions = list(
            Question.objects.filter(topic=topic, source='pyq')
        )

        selected_questions = []

        # Case 1: Enough PYQs
        if len(pyq_questions) >= num_questions:
            selected_questions = random.sample(pyq_questions, num_questions)

        else:
            # Case 2: Partial or No PYQs
            selected_questions = pyq_questions

            remaining = num_questions - len(pyq_questions)

            # 🔹 Generate LLM questions
            llm_questions = MockTestService._generate_llm_questions(
                topic=topic,
                count=remaining
            )

            selected_questions.extend(llm_questions)

        # 🔹 Create test
        with transaction.atomic():

            mock_test = MockTest.objects.create(
                user=user,
                title=f"{topic.name} Practice Test",
                description=f"{topic.name} Topic Test",
                duration_minutes=duration_minutes,
                status='active'
            )

            total_marks = 0

            for q in selected_questions:
                mock_test.questions.add(q)
                total_marks += q.marks if hasattr(q, "marks") else 1

            mock_test.total_marks = total_marks
            mock_test.question_count = len(selected_questions)
            mock_test.save()

        return mock_test
    @staticmethod
    def _generate_llm_questions(topic, count):
        client = Groq(api_key=settings.GROQ_API_KEY)

        prompt = f"""
    Generate {count} multiple-choice questions for topic: {topic.name}

    Return ONLY JSON array. No explanation, no markdown.

    Format:
    [
    {{
        "question_text": "...",
        "options": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
        }},
        "correct_answer": "A",
        "explanation": "..."
    }}
    ]
    """

        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            print("RAW LLM RESPONSE:", content)  # 🔥 DEBUG

            # 🔹 Remove markdown if present
            content = re.sub(r"```json|```", "", content).strip()

            # 🔹 Extract JSON array safely
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                content = match.group(0)

            data = json.loads(content)

            questions = []

            for q in data:
                # 🔹 Validate keys
                if not all(k in q for k in ["question_text", "options", "correct_answer"]):
                    continue

                question = Question.objects.create(
                    question_text=q["question_text"],
                    options=q["options"],
                    correct_answer=q["correct_answer"],
                    explanation=q.get("explanation", ""),
                    marks=1,
                    negative_marks=0,
                    source="llm",
                    topic=topic
                )
                questions.append(question)

            if not questions:
                raise ValueError("LLM returned invalid structure")

            return questions

        except Exception as e:
            print("LLM ERROR:", str(e))

            # 🔻 HARD fallback (never fail)
            fallback = []

            for i in range(count):
                q = Question.objects.create(
                    question_text=f"[Fallback] {topic.name} Q{i+1}",
                    options={
                        "A": "Option A",
                        "B": "Option B",
                        "C": "Option C",
                        "D": "Option D",
                    },
                    correct_answer="A",
                    explanation="Fallback",
                    marks=1,
                    negative_marks=0,
                    source="llm",
                    topic=topic
                )
                fallback.append(q)

            return fallback
        
    @staticmethod
    def start_test_attempt(user, mock_test_id):
        """Start a new test attempt"""
        try:
            mock_test = MockTest.objects.get(id=mock_test_id)

            attempt = TestAttempt.objects.create(
                user=user,
                mock_test=mock_test,
                total_marks=mock_test.total_marks
            )

            if not mock_test.started_at:
                mock_test.started_at = timezone.now()
                mock_test.save()

            return attempt

        except MockTest.DoesNotExist:
            return None