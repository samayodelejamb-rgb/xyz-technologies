"""Settings shared by development and production."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def clean(value):
    """Remove spaces and quotes that often sneak into pasted values."""
    return value.strip().strip('"').strip("'").strip()


def env_bool(name, default=False):
    return clean(os.environ.get(name, str(default))).lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [clean(x) for x in os.environ.get(name, default).split(",") if clean(x)]


SECRET_KEY = clean(os.environ.get("SECRET_KEY", ""))
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "website.apps.WebsiteConfig",
    "accounts.apps.AccountsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "website.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "website.context_processors.site",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Hide the admin from the default address if you want: ADMIN_URL=manage-xyz/
ADMIN_URL = clean(os.environ.get("ADMIN_URL", "admin/")).lstrip("/")
if not ADMIN_URL.endswith("/"):
    ADMIN_URL += "/"

# ----- Accounts / client portal -----
SITE_URL = clean(os.environ.get("SITE_URL", "http://127.0.0.1:8000"))   # used in links inside emails
ACCOUNTS_REQUIRE_EMAIL_VERIFICATION = env_bool("ACCOUNTS_REQUIRE_EMAIL_VERIFICATION", True)
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home"
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24   # reset and confirmation links last 24 hours
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # stay logged in for 14 days
SESSION_COOKIE_SAMESITE = "Lax"

# ----- Email -----
EMAIL_HOST = clean(os.environ.get("EMAIL_HOST", "smtp.gmail.com"))
EMAIL_PORT = int(clean(os.environ.get("EMAIL_PORT", "587")))
EMAIL_HOST_USER = clean(os.environ.get("EMAIL_HOST_USER", ""))
EMAIL_HOST_PASSWORD = clean(os.environ.get("EMAIL_HOST_PASSWORD", "")).replace(" ", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = 10
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

MAIL_TO = clean(os.environ.get("MAIL_TO", "")) or EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = clean(os.environ.get("DEFAULT_FROM_EMAIL", "")) or EMAIL_HOST_USER or "website@localhost"

# ----- Contact form -----
CONTACT_EMAIL_ASYNC = True          # send the email in the background
CONTACT_RATE_LIMIT = 5              # messages allowed ...
CONTACT_RATE_WINDOW_MINUTES = 10    # ... per visitor in this many minutes
TRUST_PROXY = env_bool("TRUST_PROXY", False)  # True only behind a proxy that sets X-Forwarded-For

# ----- Logging -----
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False}},
}
