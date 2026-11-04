from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .emails import notify_client_staff_reply
from .models import Profile, SupportTicket, TicketReply


@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=TicketReply)
def staff_reply_created(sender, instance, created, **kwargs):
    """When staff reply in the admin: move the ticket on and email the client."""
    if not (created and instance.is_staff_reply):
        return
    ticket = instance.ticket
    if ticket.status == SupportTicket.OPEN:
        ticket.status = SupportTicket.IN_PROGRESS
    ticket.save(update_fields=["status", "updated_at"])
    notify_client_staff_reply(ticket, instance)
