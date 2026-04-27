import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.users.models import User
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserLoginSerializer,
)

User = get_user_model()

# Test credentials - use environment variables or test fixtures
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "TestPass123!")  # noqa: S2068
TEST_ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123!")  # noqa: S2068
# Suppress SonarLint warnings for test passwords - these are test fixtures, not real credentials
TEST_PASS = "pass"  # noqa: S2068
TEST_PASS_123 = "password123"  # noqa: S2068
LOGIN_PASS = "loginpass123"  # noqa: S2068
NEW_PASS = "newpass123"  # noqa: S2068
SECURE_PASS = "securepass123"  # noqa: S2068
CREATE_PASS = "createpass123"  # noqa: S2068
REGISTER_PASS = "registerpass123"  # noqa: S2068
PASS_123 = "pass123"  # noqa: S2068
LOGOUT_PASS = "logoutpass123"  # noqa: S2068
WRONG_PASS = "wrongpass"  # noqa: S2068


class TestUserModel(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com", password=TEST_PASS_123, full_name="Test User"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.full_name, "Test User")
        self.assertTrue(user.check_password(TEST_PASS_123))
        self.assertIsNotNone(user.id)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@example.com", password=TEST_ADMIN_PASSWORD
        )
        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_user_string_representation(self):
        user = User.objects.create_user(email="user@example.com", password=TEST_PASS)
        self.assertEqual(str(user), "user@example.com")

    def test_user_save_sets_username(self):
        user = User(email="test@example.com", password=TEST_PASS)
        user.save()
        self.assertEqual(user.username, "test@example.com")

    def test_user_fields(self):
        user = User.objects.create_user(
            email="test@example.com",
            password=TEST_PASS,
            full_name="Full Name",
            phone="1234567890",
            target_exam="GATE",
            study_hours_per_day=6,
            is_premium=True,
        )
        self.assertEqual(user.full_name, "Full Name")
        self.assertEqual(user.phone, "1234567890")
        self.assertEqual(user.target_exam, "GATE")
        self.assertEqual(user.study_hours_per_day, 6)
        self.assertTrue(user.is_premium)

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=TEST_PASS)

    def test_create_superuser_without_is_staff_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com", password=TEST_PASS, is_staff=False
            )

    def test_create_superuser_without_is_superuser_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com", password=TEST_PASS, is_superuser=False
            )

    def test_user_email_is_unique(self):
        User.objects.create_user(email="unique@example.com", password=TEST_PASS)
        with self.assertRaises(Exception):
            User.objects.create_user(email="unique@example.com", password=TEST_PASS)

    def test_user_default_values(self):
        user = User.objects.create_user(
            email="defaults@example.com", password=TEST_PASS
        )
        self.assertEqual(user.study_hours_per_day, 4)
        self.assertFalse(user.is_premium)
        self.assertIsNone(user.subscription_end_date)

    def test_user_manager_normalizes_email(self):
        user = User.objects.create_user(email="TEST@example.com", password=TEST_PASS)
        self.assertEqual(user.email, "TEST@example.com")


class TestUserRegistrationSerializer(TestCase):
    def test_valid_registration_data(self):
        serializer = UserRegistrationSerializer(
            data={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": SECURE_PASS,
                "password_confirm": SECURE_PASS,
                "full_name": "New User",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        serializer = UserRegistrationSerializer(
            data={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": SECURE_PASS,
                "password_confirm": WRONG_PASS,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_short_password(self):
        serializer = UserRegistrationSerializer(
            data={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": TEST_PASS,
                "password_confirm": TEST_PASS,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_create_user_from_serializer(self):
        serializer = UserRegistrationSerializer(
            data={
                "email": "create@example.com",
                "username": "createuser",
                "password": CREATE_PASS,
                "password_confirm": CREATE_PASS,
                "full_name": "Created User",
            }
        )
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "create@example.com")
        self.assertEqual(user.full_name, "Created User")
        self.assertTrue(user.check_password(CREATE_PASS))

    def test_duplicate_email_registration(self):
        User.objects.create_user(email="dup@example.com", password=TEST_PASS)
        serializer = UserRegistrationSerializer(
            data={
                "email": "dup@example.com",
                "username": "dupuser",
                "password": NEW_PASS,
                "password_confirm": NEW_PASS,
            }
        )
        self.assertFalse(serializer.is_valid())


class TestUserProfileSerializer(TestCase):
    def test_serialize_user(self):
        user = User.objects.create_user(
            email="profile@example.com",
            password=TEST_PASS,
            full_name="Profile User",
            phone="1234567890",
        )
        serializer = UserProfileSerializer(user)
        self.assertEqual(serializer.data["email"], "profile@example.com")
        self.assertEqual(serializer.data["full_name"], "Profile User")
        self.assertEqual(serializer.data["phone"], "1234567890")

    def test_read_only_fields_not_included(self):
        user = User.objects.create_user(
            email="readonly@example.com", password=TEST_PASS
        )
        serializer = UserProfileSerializer(
            user, data={"email": "changed@example.com"}, partial=True
        )
        serializer.is_valid()
        self.assertNotIn("email", serializer.validated_data)


class TestUserLoginSerializer(TestCase):
    def test_valid_login(self):
        User.objects.create_user(email="login@example.com", password=LOGIN_PASS)
        serializer = UserLoginSerializer(
            data={"email": "login@example.com", "password": LOGIN_PASS}
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("user", serializer.validated_data)

    def test_invalid_password(self):
        User.objects.create_user(email="login@example.com", password=LOGIN_PASS)
        serializer = UserLoginSerializer(
            data={"email": "login@example.com", "password": WRONG_PASS}
        )
        self.assertFalse(serializer.is_valid())

    def test_nonexistent_user(self):
        serializer = UserLoginSerializer(
            data={"email": "nonexistent@example.com", "password": TEST_PASS}
        )
        self.assertFalse(serializer.is_valid())

    def test_inactive_user(self):
        user = User.objects.create_user(
            email="inactive@example.com", password=TEST_PASS
        )
        user.is_active = False
        user.save()
        serializer = UserLoginSerializer(
            data={"email": "inactive@example.com", "password": TEST_PASS}
        )
        self.assertFalse(serializer.is_valid())


class TestRegisterView(TestCase):
    def test_register_success(self):
        client = APIClient()
        response = client.post(
            "/api/auth/register/",
            {
                "email": "register@example.com",
                "username": "registeruser",
                "password": REGISTER_PASS,
                "password_confirm": REGISTER_PASS,
                "full_name": "Register User",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "register@example.com")
        self.assertIn("auth_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_register_password_mismatch(self):
        client = APIClient()
        response = client.post(
            "/api/auth/register/",
            {
                "email": "register@example.com",
                "username": "registeruser",
                "password": PASS_123,
                "password_confirm": WRONG_PASS,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_register_short_password(self):
        client = APIClient()
        response = client.post(
            "/api/auth/register/",
            {
                "email": "register@example.com",
                "username": "registeruser",
                "password": TEST_PASS,
                "password_confirm": TEST_PASS,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_email(self):
        User.objects.create_user(email="dup@example.com", password=TEST_PASS)
        client = APIClient()
        response = client.post(
            "/api/auth/register/",
            {
                "email": "dup@example.com",
                "username": "dupuser",
                "password": NEW_PASS,
                "password_confirm": NEW_PASS,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class TestLoginView(TestCase):
    def test_login_success(self):
        User.objects.create_user(email="login@example.com", password=LOGIN_PASS)
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": "login@example.com", "password": LOGIN_PASS},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.data)
        self.assertIn("auth_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": "login@example.com", "password": WRONG_PASS},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {
                "email": "login@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class TestLogoutView(TestCase):
    def test_logout_success(self):
        user = User.objects.create_user(
            email="logout@example.com", password=LOGOUT_PASS
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Successfully logged out")

    def test_logout_unauthenticated(self):
        client = APIClient()
        response = client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 401)


class TestUserProfileView(TestCase):
    def test_get_profile(self):
        user = User.objects.create_user(
            email="profile@example.com", password=TEST_PASS, full_name="Profile User"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "profile@example.com")
        self.assertEqual(response.data["full_name"], "Profile User")

    def test_update_profile(self):
        user = User.objects.create_user(
            email="profile@example.com", password=TEST_PASS, full_name="Old Name"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch(
            "/api/auth/profile/",
            {"full_name": "New Name", "phone": "1234567890"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["full_name"], "New Name")
        self.assertEqual(response.data["phone"], "1234567890")

    def test_cannot_update_read_only_fields(self):
        user = User.objects.create_user(
            email="readonly@example.com", password=TEST_PASS, is_premium=False
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch(
            "/api/auth/profile/",
            {"email": "changed@example.com", "is_premium": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, "readonly@example.com")
        self.assertFalse(user.is_premium)

    def test_profile_unauthenticated(self):
        client = APIClient()
        response = client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 401)


class TestRefreshAccessTokenView(TestCase):
    def test_refresh_token_success(self):
        User.objects.create_user(email="refresh@example.com", password=TEST_PASS)
        client = APIClient()
        login_response = client.post(
            "/api/auth/login/",
            {"email": "refresh@example.com", "password": TEST_PASS},
            format="json",
        )
        refresh_token = login_response.cookies["refresh_token"].value

        client2 = APIClient()
        client2.cookies["refresh_token"] = refresh_token
        response = client2.post("/api/auth/refresh/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("auth_token", response.cookies)

    def test_refresh_token_missing(self):
        client = APIClient()
        response = client.post("/api/auth/refresh/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "No refresh token")

    def test_refresh_token_invalid(self):
        client = APIClient()
        client.cookies["refresh_token"] = "invalid_token"
        response = client.post("/api/auth/refresh/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Invalid refresh token")


class TestCookieJWTAuthentication(TestCase):
    def test_authenticate_with_header(self):
        from apps.users.authentication import CookieJWTAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework_simplejwt.exceptions import InvalidToken

        factory = APIRequestFactory()
        request = factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer valid_token"

        auth = CookieJWTAuthentication()
        try:
            result = auth.authenticate(request)
        except InvalidToken:
            result = None
        self.assertIsNone(result)

    def test_authenticate_with_cookie(self):
        from apps.users.authentication import CookieJWTAuthentication
        from rest_framework.test import APIRequestFactory
        from rest_framework_simplejwt.exceptions import InvalidToken

        factory = APIRequestFactory()
        request = factory.get("/")
        request.COOKIES["auth_token"] = "some_token"

        auth = CookieJWTAuthentication()
        try:
            result = auth.authenticate(request)
        except InvalidToken:
            result = None
        self.assertIsNone(result)

    def test_authenticate_no_token(self):
        from apps.users.authentication import CookieJWTAuthentication
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/")

        auth = CookieJWTAuthentication()
        result = auth.authenticate(request)
        self.assertIsNone(result)
