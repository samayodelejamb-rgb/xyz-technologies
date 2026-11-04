import re
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import SupportTicket, TicketReply

User = get_user_model()
PW = "Str0ng-pass-2026!"


def make_user(email="ada@example.com", **extra):
    return User.objects.create_user(username=email, email=email, password=PW, **extra)


@override_settings(CONTACT_EMAIL_ASYNC=False, ACCOUNTS_REQUIRE_EMAIL_VERIFICATION=True, MAIL_TO="office@example.com")
class SignupTests(TestCase):
    def signup(self, **over):
        data = {"first_name": "Ada", "email": "Ada@Example.com", "password1": PW, "password2": PW, "nickname": ""}
        data.update(over)
        return self.client.post(reverse("accounts:signup"), data)

    def test_signup_creates_inactive_user_and_sends_link(self):
        response = self.signup()
        self.assertRedirects(response, reverse("accounts:signup_done"))
        user = User.objects.get(username="ada@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ada@example.com"])

    def test_activation_link_works_and_login_follows(self):
        self.signup()
        link = re.search(r"https?://\S+/account/activate/\S+", mail.outbox[0].body).group(0)
        self.client.get(urlparse(link).path)
        self.assertTrue(User.objects.get(username="ada@example.com").is_active)
        response = self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": PW})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_cannot_log_in_before_verifying(self):
        self.signup()
        response = self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": PW})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "verify your email")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_duplicate_email_is_rejected(self):
        make_user("ada@example.com")
        response = self.signup()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_weak_password_is_rejected(self):
        response = self.signup(password1="12345678", password2="12345678")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="ada@example.com").exists())

    def test_honeypot_creates_no_account(self):
        self.signup(nickname="bot")
        self.assertFalse(User.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_activation_link(self):
        response = self.client.get(reverse("accounts:activate", args=["abc", "bad-token"]))
        self.assertEqual(response.status_code, 400)


class LoginTests(TestCase):
    def test_login_and_logout(self):
        make_user()
        login = reverse("accounts:login")
        response = self.client.post(login, {"username": "ADA@example.com", "password": PW})
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_account_locks_after_five_wrong_passwords(self):
        make_user()
        login = reverse("accounts:login")
        for _ in range(5):
            self.client.post(login, {"username": "ada@example.com", "password": "wrong-password"})
        response = self.client.post(login, {"username": "ada@example.com", "password": PW})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "temporarily locked")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_portal_requires_login(self):
        dashboard = reverse("accounts:dashboard")
        response = self.client.get(dashboard)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={dashboard}")

    def test_password_reset_sends_email(self):
        make_user()
        with override_settings(CONTACT_EMAIL_ASYNC=False):
            response = self.client.post(reverse("accounts:password_reset"), {"email": "ada@example.com"})
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/account/reset/", mail.outbox[0].body)


@override_settings(CONTACT_EMAIL_ASYNC=False, MAIL_TO="office@example.com")
class TicketTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_create_ticket_notifies_staff(self):
        response = self.client.post(reverse("accounts:ticket_new"), {
            "subject": "Printer down", "category": "IT support", "message": "The office printer stopped working today.",
        })
        ticket = SupportTicket.objects.get()
        self.assertRedirects(response, ticket.get_absolute_url())
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(mail.outbox[0].to, ["office@example.com"])

    def test_other_users_cannot_open_my_ticket(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="Private", message="Secret details here")
        other = make_user("other@example.com")
        self.client.force_login(other)
        self.assertEqual(self.client.get(ticket.get_absolute_url()).status_code, 404)

    def test_client_reply_reopens_resolved_ticket(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="Wi-Fi", message="Wi-Fi is slow in room 4",
                                              status=SupportTicket.RESOLVED)
        self.client.post(ticket.get_absolute_url(), {"message": "Still slow, please check again."})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, SupportTicket.OPEN)
        self.assertEqual(ticket.replies.count(), 1)

    def test_closed_ticket_rejects_replies(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="Done", message="All finished now",
                                              status=SupportTicket.CLOSED)
        self.client.post(ticket.get_absolute_url(), {"message": "One more thing please"})
        self.assertEqual(ticket.replies.count(), 0)

    def test_staff_reply_emails_client_and_updates_status(self):
        ticket = SupportTicket.objects.create(user=self.user, subject="Server", message="Server is not responding")
        staff = make_user("staff@example.com", is_staff=True)
        TicketReply.objects.create(ticket=ticket, author=staff, message="We are on it.", is_staff_reply=True)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, SupportTicket.IN_PROGRESS)
        self.assertEqual(mail.outbox[-1].to, ["ada@example.com"])

    def test_profile_update(self):
        self.client.post(reverse("accounts:profile"), {
            "first_name": "Ada", "last_name": "Obi", "phone": "+234 801 234 5678", "company": "Obi Schools",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, "Obi")
        self.assertEqual(self.user.profile.company, "Obi Schools")
