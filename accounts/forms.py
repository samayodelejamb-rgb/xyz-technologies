from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.template.loader import render_to_string

from website.forms import PHONE_PATTERN

from .emails import send_plain
from .models import Profile, SupportTicket

User = get_user_model()

HONEYPOT = forms.CharField(
    required=False, label="Leave this empty",
    widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
)


class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=60, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    email = forms.EmailField(max_length=150, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1 = forms.CharField(
        label="Password", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirm password", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    nickname = HONEYPOT

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Try logging in.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords do not match.")
        elif p1:
            candidate = User(username=cleaned.get("email", ""), email=cleaned.get("email", ""),
                             first_name=cleaned.get("first_name", ""))
            try:
                password_validation.validate_password(p1, candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self):
        data = self.cleaned_data
        verify = settings.ACCOUNTS_REQUIRE_EMAIL_VERIFICATION
        user = User.objects.create_user(
            username=data["email"], email=data["email"], password=data["password1"],
            first_name=data["first_name"].strip(), is_active=not verify,
        )
        if not verify:
            profile = Profile.for_user(user)
            profile.email_verified = True
            profile.save(update_fields=["email_verified"])
        return user


class EmailAuthenticationForm(AuthenticationForm):
    """Log in with email + password. Locks the account after repeated wrong passwords."""

    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        user = User.objects.filter(username=email).first() if email else None
        profile = Profile.for_user(user) if user else None

        if profile and profile.is_locked():
            raise forms.ValidationError(
                "This account is temporarily locked after too many wrong passwords. "
                "Please try again in %d minutes or reset your password." % Profile.LOCK_MINUTES,
                code="locked",
            )
        if user and password and not user.is_active and not profile.email_verified and user.check_password(password):
            raise forms.ValidationError(
                "Please verify your email address first. Check your inbox for the confirmation link.",
                code="unverified",
            )
        try:
            return super().clean()
        except forms.ValidationError:
            if profile and password:
                profile.register_failure()
            raise


class ResendActivationForm(forms.Form):
    email = forms.EmailField(max_length=150)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class SafePasswordResetForm(PasswordResetForm):
    """Same as Django's, but an email problem never crashes the page."""

    def send_mail(self, subject_template_name, email_template_name, context, from_email,
                  to_email, html_email_template_name=None):
        context["site_url"] = settings.SITE_URL.rstrip("/")
        subject = "".join(render_to_string(subject_template_name, context).splitlines())
        body = render_to_string(email_template_name, context)
        send_plain(subject, body, [to_email])


class AccountForm(forms.Form):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60, required=False)
    phone = forms.CharField(max_length=30, required=False)
    company = forms.CharField(max_length=120, required=False)

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone


class TicketForm(forms.ModelForm):
    message = forms.CharField(min_length=10, max_length=3000, widget=forms.Textarea(attrs={"rows": 6}))

    class Meta:
        model = SupportTicket
        fields = ["subject", "category", "message"]


class ReplyForm(forms.Form):
    message = forms.CharField(min_length=2, max_length=3000, widget=forms.Textarea(attrs={"rows": 4}), label="Your reply")
