"""Production settings (PostgreSQL, HTTPS, security headers)."""
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

if len(SECRET_KEY) < 40:
    raise ImproperlyConfigured("SECRET_KEY is missing or too short (use at least 40 random characters).")

DEBUG = False

# Render tells each service its own address in these two variables.
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

SITE_URL = clean(os.environ.get("SITE_URL", "")) or RENDER_URL  # noqa: F405
if not SITE_URL.startswith("https://"):
    raise ImproperlyConfigured("Set SITE_URL to your public address, for example: https://yourdomain.com")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")  # noqa: F405
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Set ALLOWED_HOSTS, for example: yourdomain.com,www.yourdomain.com")

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")  # noqa: F405
if RENDER_URL:
    CSRF_TRUSTED_ORIGINS.append(RENDER_URL)

if not os.environ.get("DATABASE_URL"):
    raise ImproperlyConfigured("Set DATABASE_URL, for example: postgres://user:password@host:5432/dbname")
DATABASES = {"default": dj_database_url.config(conn_max_age=600, conn_health_checks=True)}

# Static files are served by WhiteNoise (compressed + cache-busting file names)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ----- HTTPS and cookies -----
FORCE_HTTPS = env_bool("FORCE_HTTPS", True)  # noqa: F405
SECURE_SSL_REDIRECT = FORCE_HTTPS
SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = FORCE_HTTPS
CSRF_COOKIE_SECURE = FORCE_HTTPS
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = int(os.environ.get("HSTS_SECONDS", "3600")) if FORCE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("HSTS_INCLUDE_SUBDOMAINS", False)  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"