from django.utils import timezone
from django.db.models import Q
from .models import Question, MockTest, TestAttempt, Answer
import random


class MockTestService:
    """Service layer for mock test operations"""
    
    @staticmethod
    def create_mock_test(user, title, exam_type, subject, difficulty, 
                        num_questions, duration_minutes=60):
        """Create a new mock test with selected questions"""
        
        # Fetch questions based on criteria
        questions = Question.objects.filter(
            exam_type=exam_type,
            subject=subject,
            difficulty=difficulty
        ).order_by('?')[:num_questions]  # Random selection
        
        if questions.count() < num_questions:
            # If not enough questions, fetch mixed difficulty
            questions = Question.objects.filter(
                exam_type=exam_type,
                subject=subject
            ).order_by('?')[:num_questions]
        
        # Create mock test
        mock_test = MockTest.objects.create(
            user=user,
            title=title,
            exam_type=exam_type,
            description=f"{subject} - {difficulty.capitalize()} level test",
            duration_minutes=duration_minutes,
            status='active'
        )
        
        # Add questions and calculate total marks
        total_marks = 0
        for question in questions:
            mock_test.questions.add(question)
            total_marks += question.marks
        
        mock_test.total_marks = total_marks
        mock_test.save()
        
        return mock_test
    
    @staticmethod
    def start_test_attempt(user, mock_test_id):
        """Start a new test attempt"""
        try:
            mock_test = MockTest.objects.get(id=mock_test_id)
            
            # Create attempt
            attempt = TestAttempt.objects.create(
                user=user,
                mock_test=mock_test,
                total_marks=mock_test.total_marks
            )
            
            # Update mock test status
            if not mock_test.started_at:
                mock_test.started_at = timezone.now()
                mock_test.save()
            
            return attempt
        except MockTest.DoesNotExist:
            return None
    
    @staticmethod
    def submit_answer(attempt_id, question_id, user_answer, time_taken_seconds=0):
        """Submit an answer for a question"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
            question = Question.objects.get(id=question_id)
            
            # Check if answer is correct
            is_correct = MockTestService._check_answer(
                question, 
                user_answer
            )
            
            # Calculate marks
            marks_obtained = 0
            if is_correct:
                marks_obtained = question.marks
            elif user_answer:  # Answered but wrong
                marks_obtained = -question.negative_marks
            
            # Create or update answer
            answer, created = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'marks_obtained': marks_obtained,
                    'time_taken_seconds': time_taken_seconds
                }
            )
            
            return answer
        except (TestAttempt.DoesNotExist, Question.DoesNotExist):
            return None
    
    @staticmethod
    def _check_answer(question, user_answer):
        """Check if the answer is correct"""
        if not user_answer:
            return False
        
        correct = question.correct_answer.strip().lower()
        given = user_answer.strip().lower()
        
        return correct == given
    
    @staticmethod
    def finalize_test(attempt_id):
        """Calculate final score and mark test as completed"""
        try:
            attempt = TestAttempt.objects.get(id=attempt_id)
            
            # Calculate statistics
            answers = attempt.answers.all()
            total_questions = answers.count()
            
            correct = answers.filter(is_correct=True).count()
            incorrect = answers.filter(
                is_correct=False, 
                user_answer__isnull=False
            ).exclude(user_answer='').count()
            unanswered = total_questions - (correct + incorrect)
            
            # Calculate score
            total_score = sum([ans.marks_obtained for ans in answers])
            percentage = (total_score / attempt.total_marks * 100) if attempt.total_marks > 0 else 0
            
            # Calculate time taken
            time_taken = (timezone.now() - attempt.started_at).total_seconds() / 60
            
            # Update attempt
            attempt.submitted_at = timezone.now()
            attempt.score = total_score
            attempt.percentage = max(0, percentage)  # Don't show negative percentage
            attempt.correct_answers = correct
            attempt.incorrect_answers = incorrect
            attempt.unanswered = unanswered
            attempt.time_taken_minutes = int(time_taken)
            attempt.save()
            
            # Update mock test status
            mock_test = attempt.mock_test
            mock_test.status = 'completed'
            mock_test.completed_at = timezone.now()
            mock_test.save()
            
            return attempt
        except TestAttempt.DoesNotExist:
            return None
    
    @staticmethod
    def generate_ai_questions(exam_type, subject, topic, difficulty, num_questions):
        """
        Generate questions using AI
        This will be implemented with AI service integration
        """
        from apps.ai_service.services import AIService
        
        prompt = f"""
        Generate {num_questions} {difficulty} level questions for {exam_type} exam.
        
        Subject: {subject}
        Topic: {topic or 'Any'}
        
        Return JSON array with this structure:
        [
            {{
                "question_text": "Question here?",
                "question_type": "mcq",
                "option_a": "Option A",
                "option_b": "Option B",
                "option_c": "Option C",
                "option_d": "Option D",
                "correct_answer": "A",
                "explanation": "Explanation here",
                "marks": 1
            }},
            ...
        ]
        """
        
        try:
            questions_data = AIService.generate_questions(
                prompt=prompt,
                context=f"{exam_type} - {subject}"
            )
            
            # Create question objects
            created_questions = []
            for q_data in questions_data:
                question = Question.objects.create(
                    subject=subject,
                    topic=topic or subject,
                    exam_type=exam_type,
                    difficulty=difficulty,
                    **q_data
                )
                created_questions.append(question)
            
            return created_questions
        except Exception as e:
            # Return empty list if AI generation fails
            return []
