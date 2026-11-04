"""Local development settings (SQLite, debug on)."""
from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = SECRET_KEY or "dev-insecure-key-only-for-local-use"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
