"""All emails sent by the client portal. Failures are logged, never shown as a crash."""
import logging
import threading

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

logger = logging.getLogger(__name__)


def site_url():
    return settings.SITE_URL.rstrip("/")


def _send(subject, body, to, reply_to):
    try:
        EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL,
                     to=to, reply_to=reply_to or None).send(fail_silently=False)
    except Exception:
        logger.exception("Email failed: %s", subject)


def send_plain(subject, body, to, reply_to=None):
    """Send in the background (or immediately when CONTACT_EMAIL_ASYNC is False)."""
    if not [address for address in to if address]:
        return
    if settings.CONTACT_EMAIL_ASYNC:
        threading.Thread(target=_send, args=(subject, body, to, reply_to), daemon=True).start()
    else:
        _send(subject, body, to, reply_to)


def send_activation_email(user):
    from .models import Profile

    profile = Profile.for_user(user)
    profile.activation_sent_at = timezone.now()
    profile.save(update_fields=["activation_sent_at"])

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = site_url() + reverse("accounts:activate", args=[uid, token])
    body = (
        f"Hello {user.first_name or 'there'},\n\n"
        "Thank you for creating an account with XYZ Technologies Limited.\n"
        f"Please confirm your email address by opening this link:\n\n{link}\n\n"
        "If you did not create this account, you can ignore this email.\n"
    )
    send_plain("Confirm your XYZ Technologies account", body, [user.email])


def notify_staff_new_ticket(ticket):
    body = (
        f"New support request {ticket.reference}\n\n"
        f"From:     {ticket.user.get_full_name() or ticket.user.email} <{ticket.user.email}>\n"
        f"Category: {ticket.category}\n"
        f"Subject:  {ticket.subject}\n\n{ticket.message}\n\n"
        f"Reply in the admin: {site_url()}/{settings.ADMIN_URL}accounts/supportticket/{ticket.pk}/change/\n"
    )
    send_plain(f"[{ticket.reference}] New request: {ticket.subject}", body, [settings.MAIL_TO], [ticket.user.email])


def notify_staff_reply(ticket, reply):
    body = (
        f"{ticket.user.email} replied on {ticket.reference} ({ticket.subject}):\n\n{reply.message}\n\n"
        f"Open in the admin: {site_url()}/{settings.ADMIN_URL}accounts/supportticket/{ticket.pk}/change/\n"
    )
    send_plain(f"[{ticket.reference}] Client reply", body, [settings.MAIL_TO], [ticket.user.email])


def notify_client_staff_reply(ticket, reply):
    body = (
        f"Hello {ticket.user.first_name or 'there'},\n\n"
        f"We replied to your request {ticket.reference} ({ticket.subject}):\n\n{reply.message}\n\n"
        f"View the full conversation: {site_url()}{ticket.get_absolute_url()}\n"
    )
    send_plain(f"[{ticket.reference}] We replied to your request", body, [ticket.user.email])
