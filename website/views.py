import ipaddress
import json
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .emailing import dispatch_contact_email
from .forms import ContactForm
from .models import (
    TOPICS, ContactMessage, Milestone, Product, Project, Service,
    Stat, TeamMember, Testimonial, Value,
)

OK_TEXT = "Thank you! Your message has been sent. We will reply within one working day."


class PageView(TemplateView):
    page_title = ""
    page_description = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["page_description"] = self.page_description
        return context


class HomeView(PageView):
    template_name = "home.html"
    page_description = "Software development, networking, cybersecurity, IT support and technology products in Abeokuta, Ogun State."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = Stat.published.all()
        context["services"] = Service.published.all()[:3]
        context["testimonials"] = Testimonial.published.all()[:2]
        return context


class AboutView(PageView):
    template_name = "about.html"
    page_title = "About us"
    page_description = "Who we are, our mission and vision, our values and the team behind XYZ Technologies Limited."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["values"] = Value.published.all()
        context["milestones"] = Milestone.published.all()
        context["team"] = TeamMember.published.all()
        return context


class ServicesView(PageView):
    template_name = "services.html"
    page_title = "Services"
    page_description = "Software development, networking, cybersecurity, IT support, CCTV and training."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = Service.published.all()
        return context


class ProductsView(PageView):
    template_name = "products.html"
    page_title = "Products"
    page_description = "Software products and hardware supplied and installed by XYZ Technologies Limited."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["software"] = Product.published.filter(category=Product.SOFTWARE)
        context["hardware"] = Product.published.filter(category=Product.HARDWARE)
        return context


class ProjectsView(PageView):
    template_name = "projects.html"
    page_title = "Projects"
    page_description = "Selected projects and client feedback from across Abeokuta and Ogun State."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = Project.published.all()
        context["testimonials"] = Testimonial.published.all()
        return context


class ContactView(PageView):
    template_name = "contact.html"
    page_title = "Contact us"
    page_description = "Contact XYZ Technologies Limited in Abeokuta for a free consultation."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topics"] = TOPICS
        return context


# ---------- contact form API ----------
def client_ip(request):
    value = request.META.get("REMOTE_ADDR", "")
    if settings.TRUST_PROXY:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        value = forwarded.split(",")[0].strip() or value
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def is_rate_limited(ip):
    if not ip:
        return False
    since = timezone.now() - timedelta(minutes=settings.CONTACT_RATE_WINDOW_MINUTES)
    recent = ContactMessage.objects.filter(ip=ip, created_at__gte=since).count()
    return recent >= settings.CONTACT_RATE_LIMIT


FIELD_ERRORS = {
    "name": "Please enter your name (up to 100 characters).",
    "email": "Please enter a valid email address.",
    "phone": "Please enter a valid phone number.",
    "message": "Please enter a message of 10 to 3000 characters.",
}


@require_POST
def contact_send(request):
    ip = client_ip(request)
    if is_rate_limited(ip):
        return JsonResponse({"ok": False, "error": "Too many messages. Please try again later."}, status=429)

    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid request."}, status=400)

    # Hidden trap field: real visitors never fill it, bots usually do.
    if str(data.get("nickname", "")).strip():
        return JsonResponse({"ok": True, "message": OK_TEXT})

    if data.get("topic") not in TOPICS:
        data["topic"] = "Other"

    form = ContactForm(data)
    if not form.is_valid():
        field = next(iter(form.errors))
        return JsonResponse({"ok": False, "error": FIELD_ERRORS.get(field, "Please check the form.")}, status=400)

    item = form.save(commit=False)
    item.ip = ip
    item.user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]
    item.save()

    dispatch_contact_email(item.pk)
    return JsonResponse({"ok": True, "message": OK_TEXT})


# ---------- utility endpoints ----------
@require_GET
def healthz(request):
    """Used by hosting platforms to check the site and database are alive."""
    try:
        connection.ensure_connection()
    except Exception:
        return HttpResponse("database unavailable", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        f"Disallow: /{settings.ADMIN_URL}",
        "Disallow: /account/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
