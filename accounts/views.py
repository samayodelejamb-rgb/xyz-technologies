from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_http_methods

from website.models import SiteSettings

from .emails import notify_staff_new_ticket, notify_staff_reply, send_activation_email
from .forms import (
    AccountForm, EmailAuthenticationForm, ReplyForm, ResendActivationForm,
    SignUpForm, TicketForm,
)
from .models import Profile, SupportTicket, TicketReply

User = get_user_model()
TICKETS_PER_HOUR = 10


# ---------- sign up and email verification ----------
def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("nickname"):  # bots fill the hidden field
            return redirect("accounts:signup_done")
        user = form.save()
        if settings.ACCOUNTS_REQUIRE_EMAIL_VERIFICATION:
            send_activation_email(user)
        return redirect("accounts:signup_done")
    return render(request, "accounts/signup.html", {"form": form})


def signup_done(request):
    return render(request, "accounts/signup_done.html", {"verify": settings.ACCOUNTS_REQUIRE_EMAIL_VERIFICATION})


def activate(request, uidb64, token):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return render(request, "accounts/activation_invalid.html", status=400)

    profile = Profile.for_user(user)
    if profile.email_verified:
        # Already verified. Never re-enable an account that staff switched off.
        messages.info(request, "This email address was already verified. You can log in.")
    else:
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "Email verified. You can now log in.")
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def resend_activation(request):
    form = ResendActivationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(username=form.cleaned_data["email"], is_active=False).first()
        if user:
            profile = Profile.for_user(user)
            if not profile.email_verified and profile.can_resend_activation():
                send_activation_email(user)
        # Same answer either way, so nobody can test which emails have accounts
        messages.info(request, "If that account is waiting for verification, we have sent a new link.")
        return redirect("accounts:login")
    return render(request, "accounts/resend_activation.html", {"form": form})


# ---------- login ----------
class PortalLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Django's LoginView puts its own "site" object in the context, which hides our
        # company settings. Put ours back so the header, footer and title work.
        context["site"] = SiteSettings.load()
        return context

    def form_valid(self, form):
        Profile.for_user(form.get_user()).reset_failures()
        return super().form_valid(form)


# ---------- portal ----------
@login_required
def dashboard(request):
    tickets = request.user.tickets.all()
    open_count = tickets.exclude(status__in=[SupportTicket.RESOLVED, SupportTicket.CLOSED]).count()
    return render(request, "accounts/dashboard.html", {"tickets": tickets, "open_count": open_count})


@login_required
def ticket_new(request):
    form = TicketForm(request.POST or None)
    if request.method == "POST":
        since = timezone.now() - timedelta(hours=1)
        if SupportTicket.objects.filter(user=request.user, created_at__gte=since).count() >= TICKETS_PER_HOUR:
            messages.error(request, "You have sent many requests in the last hour. Please try again later.")
        elif form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            notify_staff_new_ticket(ticket)
            messages.success(request, f"Request {ticket.reference} sent. We will reply as soon as we can.")
            return redirect(ticket)
    return render(request, "accounts/ticket_form.html", {"form": form})


@login_required
def ticket_detail(request, pk):
    # Only the owner can open a ticket: anyone else gets a 404
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    form = ReplyForm(request.POST or None)

    if request.method == "POST":
        if ticket.is_closed:
            messages.error(request, "This request is closed. Please open a new one.")
            return redirect(ticket)
        if form.is_valid():
            reply = TicketReply.objects.create(
                ticket=ticket, author=request.user, message=form.cleaned_data["message"], is_staff_reply=False,
            )
            if ticket.status == SupportTicket.RESOLVED:
                ticket.status = SupportTicket.OPEN  # client answered: reopen
            ticket.save(update_fields=["status", "updated_at"])
            notify_staff_reply(ticket, reply)
            messages.success(request, "Reply sent.")
            return redirect(ticket)

    return render(request, "accounts/ticket_detail.html", {
        "ticket": ticket, "replies": ticket.replies.select_related("author"), "form": form,
    })


@login_required
def profile(request):
    prof = Profile.for_user(request.user)
    initial = {
        "first_name": request.user.first_name, "last_name": request.user.last_name,
        "phone": prof.phone, "company": prof.company,
    }
    form = AccountForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        request.user.first_name = data["first_name"].strip()
        request.user.last_name = data["last_name"].strip()
        request.user.save(update_fields=["first_name", "last_name"])
        prof.phone, prof.company = data["phone"], data["company"].strip()
        prof.save(update_fields=["phone", "company"])
        messages.success(request, "Your details were saved.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})