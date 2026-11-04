FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

# Collect static files at build time (temporary values, only used for this step)
RUN SECRET_KEY=build-only-key-build-only-key-build-only-key-0123456789 \
    ALLOWED_HOSTS=localhost \
    SITE_URL=https://localhost \
    DATABASE_URL=sqlite:////tmp/build.db \
    python manage.py collectstatic --noinput

RUN useradd --create-home app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 30 --access-logfile -"]
