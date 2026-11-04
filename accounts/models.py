from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from website.models import TOPICS


class Profile(models.Model):
    """Extra details and login-safety fields for every user."""

    MAX_FAILURES = 5
    LOCK_MINUTES = 15
    RESEND_MINUTES = 5

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=120, blank=True)

    email_verified = models.BooleanField(default=False)
    activation_sent_at = models.DateTimeField(null=True, blank=True)
    failed_logins = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user}"

    @classmethod
    def for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failure(self):
        self.failed_logins += 1
        if self.failed_logins >= self.MAX_FAILURES:
            self.locked_until = timezone.now() + timedelta(minutes=self.LOCK_MINUTES)
            self.failed_logins = 0
        self.save(update_fields=["failed_logins", "locked_until"])

    def reset_failures(self):
        if self.failed_logins or self.locked_until:
            self.failed_logins = 0
            self.locked_until = None
            self.save(update_fields=["failed_logins", "locked_until"])

    def can_resend_activation(self):
        if not self.activation_sent_at:
            return True
        return timezone.now() - self.activation_sent_at > timedelta(minutes=self.RESEND_MINUTES)


class SupportTicket(models.Model):
    OPEN, IN_PROGRESS, RESOLVED, CLOSED = "open", "in_progress", "resolved", "closed"
    STATUSES = [(OPEN, "Open"), (IN_PROGRESS, "In progress"), (RESOLVED, "Resolved"), (CLOSED, "Closed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=[(t, t) for t in TOPICS], default="IT support")
    message = models.TextField()
    status = models.CharField(max_length=12, choices=STATUSES, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.reference}: {self.subject}"

    @property
    def reference(self):
        return f"T-{self.pk:05d}"

    @property
    def is_closed(self):
        return self.status == self.CLOSED

    def get_absolute_url(self):
        return reverse("accounts:ticket_detail", args=[self.pk])


class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ticket_replies")
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "ticket replies"

    def __str__(self):
        return f"Reply on {self.ticket.reference}"
