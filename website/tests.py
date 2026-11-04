import json

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, Service

GOOD = {
    "name": "Ada Obi", "email": "ada@example.com", "phone": "+234 801 234 5678",
    "topic": "Networking", "message": "We need Wi-Fi installed in our school.",
}


def post_json(client, data):
    return client.post(reverse("contact_send"), data=json.dumps(data), content_type="application/json")


class PageTests(TestCase):
    def test_all_pages_load(self):
        for name in ["home", "about", "services", "products", "projects", "contact"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_unpublished_service_is_hidden(self):
        Service.objects.create(title="Visible service", summary="x")
        Service.objects.create(title="Hidden service", summary="x", is_published=False)
        page = self.client.get(reverse("services"))
        self.assertContains(page, "Visible service")
        self.assertNotContains(page, "Hidden service")

    def test_utility_endpoints(self):
        self.assertEqual(self.client.get(reverse("healthz")).status_code, 200)
        self.assertContains(self.client.get(reverse("robots")), "Sitemap:")
        self.assertEqual(self.client.get(reverse("sitemap")).status_code, 200)

    def test_unknown_page_is_404(self):
        self.assertEqual(self.client.get("/no-such-page/").status_code, 404)


@override_settings(CONTACT_EMAIL_ASYNC=False, MAIL_TO="office@example.com")
class ContactTests(TestCase):
    def test_valid_message_is_saved_and_emailed(self):
        response = post_json(self.client, GOOD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["office@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["ada@example.com"])
        self.assertTrue(ContactMessage.objects.get().email_sent)

    def test_invalid_email_is_rejected(self):
        response = post_json(self.client, {**GOOD, "email": "nope"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_short_message_is_rejected(self):
        self.assertEqual(post_json(self.client, {**GOOD, "message": "hi"}).status_code, 400)

    def test_bad_json_is_rejected(self):
        response = self.client.post(reverse("contact_send"), data="not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_honeypot_bots_are_ignored(self):
        response = post_json(self.client, {**GOOD, "nickname": "spam-bot"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertEqual(post_json(self.client, GOOD).status_code, 200)
        self.assertEqual(post_json(self.client, GOOD).status_code, 429)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(reverse("contact_send")).status_code, 405)
