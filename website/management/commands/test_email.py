"""Check your email settings.   Usage:  python manage.py test_email you@example.com"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sends a test email and prints the exact error if it fails."

    def add_arguments(self, parser):
        parser.add_argument("to", nargs="?", default=None, help="Address to send to (default: MAIL_TO)")

    def handle(self, *args, **options):
        to = options["to"] or settings.MAIL_TO
        backend = settings.EMAIL_BACKEND.rsplit(".", 2)[-2]
        self.stdout.write(f"Backend:   {backend}")
        self.stdout.write(f"Host:      {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (TLS={settings.EMAIL_USE_TLS})")
        self.stdout.write(f"Login:     {settings.EMAIL_HOST_USER or '(empty)'}")
        self.stdout.write(f"Password:  {'set, ' + str(len(settings.EMAIL_HOST_PASSWORD)) + ' characters' if settings.EMAIL_HOST_PASSWORD else '(empty)'}")
        self.stdout.write(f"From:      {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"To:        {to or '(empty)'}")

        if backend == "console":
            self.stdout.write(self.style.WARNING(
                "\nNo email login found, so emails only print in the terminal. "
                "Check that .env is in the same folder as manage.py and that "
                "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are filled in."))
        if not to:
            self.stderr.write(self.style.ERROR("\nNo recipient. Set MAIL_TO in .env or pass an address."))
            return

        try:
            send_mail("XYZ website test email", "If you can read this, email works.",
                      settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
        except Exception as error:
            self.stderr.write(self.style.ERROR(f"\nSending FAILED: {type(error).__name__}: {error}"))
            return
        self.stdout.write(self.style.SUCCESS(f"\nSent to {to}. Check the inbox and the Spam folder."))
