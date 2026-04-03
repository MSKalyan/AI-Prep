import pytest
from datetime import date, timedelta

@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email='test@example.com',
        password='testpass123',
        full_name='Test User'
    )

@pytest.fixture
def user2(django_user_model):
    return django_user_model.objects.create_user(
        email='test2@example.com',
        password='testpass123',
        full_name='Test User 2'
    )

@pytest.fixture
def exam(db):
    from apps.roadmap.models import Exam
    return Exam.objects.create(
        name="GATE CS",
        category="Engineering",
        total_marks=100,
        exam_date=date.today() + timedelta(days=180)
    )

@pytest.fixture
def subject(db, exam):
    from apps.roadmap.models import Subject
    return Subject.objects.create(
        exam=exam,
        name="Data Structures",
        order=1
    )

@pytest.fixture
def topic(db, subject):
    from apps.roadmap.models import Topic
    return Topic.objects.create(
        name="Arrays",
        subject=subject,
        weightage=5.0,
        pyq_count=10,
        is_core=True
    )

@pytest.fixture
def roadmap(db, user, exam):
    from apps.roadmap.models import Roadmap
    return Roadmap.objects.create(
        user=user,
        exam=exam,
        target_date=date.today() + timedelta(days=90),
        total_weeks=12,
        is_active=True
    )

@pytest.fixture
def mock_test(db, user, exam):
    from apps.mocktest.models import MockTest
    return MockTest.objects.create(
        user=user,
        title="Test Mock",
        exam=exam,
        total_marks=50,
        question_count=10,
        duration_minutes=60,
        status='active'
    )

@pytest.fixture
def question(db, topic, exam):
    from apps.mocktest.models import Question
    return Question.objects.create(
        topic=topic,
        exam=exam,
        question_text="What is an array?",
        question_type="mcq",
        options={"A": "Data structure", "B": "Function", "C": "Loop"},
        correct_answer="A",
        explanation="Arrays store elements",
        difficulty="easy",
        marks=1,
        source="llm"
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
