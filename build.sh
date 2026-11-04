#!/usr/bin/env bash
# Runs on every deploy (Render "build command").
set -o errexit

pip install -r requirements-prod.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Create the admin user from the DJANGO_SUPERUSER_* variables (skipped if it already exists)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || echo "Admin user already exists, skipping."
fi

# Optional sample content (only fills EMPTY tables)
if [ "$SEED_SAMPLE_CONTENT" = "true" ]; then
  python manage.py seed_content
fi