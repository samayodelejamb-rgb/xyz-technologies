"""Sends the contact message to the company inbox."""
import logging
import threading

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import close_old_connections

from .models import ContactMessage

logger = logging.getLogger(__name__)


def deliver_contact_email(message_id):
    """Email one saved message. Records success or the exact error on the message."""
    try:
        item = ContactMessage.objects.get(pk=message_id)
        if not settings.MAIL_TO:
            item.email_error = "MAIL_TO is not set."
            item.save(update_fields=["email_error"])
            return False

        body = (
            f"Name:  {item.name}\n"
            f"Email: {item.email}\n"
            f"Phone: {item.phone or '-'}\n"
            f"Topic: {item.topic}\n"
            f"Sent:  {item.created_at:%d %b %Y, %H:%M}\n\n"
            f"{item.message}\n"
        )
        EmailMessage(
            subject=f"Website enquiry: {item.topic} ({item.name})",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.MAIL_TO],
            reply_to=[item.email],  # pressing Reply goes to the visitor
        ).send(fail_silently=False)

        item.email_sent = True
        item.email_error = ""
        item.save(update_fields=["email_sent", "email_error"])
        return True
    except Exception as error:  # never lose the message because email failed
        logger.exception("Contact email failed for message %s", message_id)
        try:
            ContactMessage.objects.filter(pk=message_id).update(email_error=str(error)[:255])
        except Exception:
            pass
        return False
    finally:
        close_old_connections()


def dispatch_contact_email(message_id):
    """Send in the background so the visitor does not wait for the mail server."""
    if settings.CONTACT_EMAIL_ASYNC:
        threading.Thread(target=deliver_contact_email, args=(message_id,), daemon=True).start()
    else:
        deliver_contact_email(message_id)
