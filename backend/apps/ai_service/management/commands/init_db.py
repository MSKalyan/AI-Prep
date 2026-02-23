"""
Initial setup script to populate database with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.ai_service.models import Document
from apps.mocktest.models import Question
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize database with sample data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Skip creating sample users',
        )
        parser.add_argument(
            '--skip-questions',
            action='store_true',
            help='Skip creating sample questions',
        )
        parser.add_argument(
            '--skip-documents',
            action='store_true',
            help='Skip creating sample documents',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database initialization...'))

        # Create sample users
        if not options['skip_users']:
            self.create_sample_users()

        # Create sample questions
        if not options['skip_questions']:
            self.create_sample_questions()

        # Create sample documents
        if not options['skip_documents']:
            self.create_sample_documents()

        self.stdout.write(self.style.SUCCESS('Database initialization complete!'))

    def create_sample_users(self):
        self.stdout.write('Creating sample users...')
        
        if not User.objects.filter(email='test@example.com').exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                full_name='Test User',
                target_exam='UPSC',
                study_hours_per_day=6
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Created test user'))

        if not User.objects.filter(email='admin@example.com').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                full_name='Admin User'
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Created admin user'))

    def create_sample_questions(self):
        self.stdout.write('Creating sample questions...')
        
        if Question.objects.count() > 0:
            self.stdout.write(self.style.WARNING('  Questions already exist, skipping...'))
            return

        subjects = ['History', 'Geography', 'Science', 'Mathematics', 'Civics']
        difficulties = ['easy', 'medium', 'hard']
        
        sample_questions = [
            {
                'subject': 'History',
                'topic': 'Ancient India',
                'question_text': 'Who was the founder of the Mauryan Empire?',
                'option_a': 'Ashoka',
                'option_b': 'Chandragupta Maurya',
                'option_c': 'Bindusara',
                'option_d': 'Samudragupta',
                'correct_answer': 'B',
                'explanation': 'Chandragupta Maurya founded the Mauryan Empire in 322 BCE.',
                'difficulty': 'easy',
                'exam_type': 'UPSC'
            },
            {
                'subject': 'Geography',
                'topic': 'Rivers of India',
                'question_text': 'Which is the longest river in India?',
                'option_a': 'Yamuna',
                'option_b': 'Brahmaputra',
                'option_c': 'Ganga',
                'option_d': 'Godavari',
                'correct_answer': 'C',
                'explanation': 'The Ganga is the longest river in India, flowing 2,525 km.',
                'difficulty': 'easy',
                'exam_type': 'UPSC'
            },
            {
                'subject': 'Science',
                'topic': 'Physics',
                'question_text': 'What is the SI unit of force?',
                'option_a': 'Joule',
                'option_b': 'Newton',
                'option_c': 'Watt',
                'option_d': 'Pascal',
                'correct_answer': 'B',
                'explanation': 'Newton (N) is the SI unit of force, named after Isaac Newton.',
                'difficulty': 'easy',
                'exam_type': 'NEET'
            },
        ]

        for q in sample_questions:
            Question.objects.create(
                question_type='mcq',
                marks=1,
                **q
            )

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(sample_questions)} sample questions'))

    def create_sample_documents(self):
        self.stdout.write('Creating sample documents...')
        
        if Document.objects.count() > 0:
            self.stdout.write(self.style.WARNING('  Documents already exist, skipping...'))
            return

        sample_docs = [
            {
                'title': 'Introduction to Indian History',
                'content': '''
                Indian history spans thousands of years, from the ancient Indus Valley
                Civilization to modern times. The Mauryan Empire (322-185 BCE) was one
                of the largest empires in Indian history, founded by Chandragupta Maurya.
                The empire reached its peak under Emperor Ashoka, who promoted Buddhism
                and non-violence after the Kalinga War.
                ''',
                'document_type': 'notes',
                'subject': 'History',
                'topic': 'Ancient India',
                'exam_type': 'UPSC'
            },
            {
                'title': 'Geography of India - Rivers',
                'content': '''
                India is blessed with numerous rivers. The Ganga, originating from
                Gangotri Glacier, is the longest river in India at 2,525 km. The
                Brahmaputra flows through Tibet, India, and Bangladesh. The Godavari
                is the largest river in peninsular India.
                ''',
                'document_type': 'notes',
                'subject': 'Geography',
                'topic': 'Rivers',
                'exam_type': 'UPSC'
            },
            {
                'title': 'Physics Fundamentals',
                'content': '''
                Force is a fundamental concept in physics. Newton's laws of motion
                describe the relationship between force, mass, and acceleration.
                The SI unit of force is Newton (N), where 1 N = 1 kg⋅m/s².
                ''',
                'document_type': 'notes',
                'subject': 'Science',
                'topic': 'Physics',
                'exam_type': 'NEET'
            },
        ]

        for doc in sample_docs:
            Document.objects.create(**doc)

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(sample_docs)} sample documents'))
