from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.models import User


class UserModelTest(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            full_name='Test User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.full_name, 'Test User')
        self.assertTrue(user.check_password('password123'))
        self.assertIsNotNone(user.id)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_user_string_representation(self):
        user = User.objects.create_user(
            email='user@example.com',
            password='pass'
        )
        self.assertEqual(str(user), 'user@example.com')

    def test_user_save_sets_username(self):
        user = User(email='test@example.com', password='pass')
        user.save()
        self.assertEqual(user.username, 'test@example.com')

    def test_user_fields(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='pass',
            full_name='Full Name',
            phone='1234567890',
            target_exam='GATE',
            study_hours_per_day=6,
            is_premium=True
        )
        self.assertEqual(user.full_name, 'Full Name')
        self.assertEqual(user.phone, '1234567890')
        self.assertEqual(user.target_exam, 'GATE')
        self.assertEqual(user.study_hours_per_day, 6)
        self.assertTrue(user.is_premium)
