"""
Test settings for running Django tests locally/CI without external services.

Key goals:
- Use SQLite (no Postgres required).
- Avoid network calls to LLM / YouTube integrations.
- Keep test runs fast and deterministic.
"""

import os

# Ensure the base settings module doesn't pick up Postgres from `.env.local`.
os.environ.setdefault("USE_LOCAL_DB", "False")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_db.sqlite3")

# Prevent any accidental external API usage during tests.
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("YOUTUBE_API_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "")

from .settings import *  # noqa: F403

# Override DB explicitly (and keep it file-based to support concurrency/migrations).
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test_db.sqlite3"),  # noqa: F405
    }
}

DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Tests should not require secure cookies/CSRF settings.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

