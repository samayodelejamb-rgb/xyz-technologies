from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import SafePasswordResetForm

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("signup/done/", views.signup_done, name="signup_done"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("resend/", views.resend_activation, name="resend_activation"),
    path("login/", views.PortalLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # POST only

    path("tickets/new/", views.ticket_new, name="ticket_new"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("profile/", views.profile, name="profile"),

    path("password-change/", auth_views.PasswordChangeView.as_view(
        template_name="accounts/password_change_form.html",
        success_url=reverse_lazy("accounts:password_change_done")), name="password_change"),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/password_change_done.html"), name="password_change_done"),

    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset_form.html",
        form_class=SafePasswordResetForm,
        email_template_name="accounts/emails/password_reset_email.txt",
        subject_template_name="accounts/emails/password_reset_subject.txt",
        success_url=reverse_lazy("accounts:password_reset_done")), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete")), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
]
