from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, SupportTicket, TicketReply

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ("phone", "company", "email_verified", "failed_logins", "locked_until")


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "first_name", "last_name", "is_active", "is_staff", "date_joined")
    actions = ["activate_users", "unlock_accounts"]

    def get_inline_instances(self, request, obj=None):
        # A profile is created automatically, so skip the inline on the "add user" page
        return super().get_inline_instances(request, obj) if obj else []

    @admin.action(description="Activate selected users (mark email as verified)")
    def activate_users(self, request, queryset):
        for user in queryset:
            profile = Profile.for_user(user)
            profile.email_verified = True
            profile.save(update_fields=["email_verified"])
        queryset.update(is_active=True)

    @admin.action(description="Unlock selected accounts")
    def unlock_accounts(self, request, queryset):
        for user in queryset:
            Profile.for_user(user).reset_failures()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class TicketReplyInline(admin.StackedInline):
    model = TicketReply
    extra = 1
    fields = ("message", "author", "is_staff_reply", "created_at")
    readonly_fields = ("author", "is_staff_reply", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "subject", "user", "category", "status", "updated_at")
    list_filter = ("status", "category", "created_at")
    list_editable = ("status",)
    list_display_links = ("reference", "subject")
    search_fields = ("subject", "message", "user__email", "user__first_name")
    readonly_fields = ("user", "subject", "category", "message", "created_at", "updated_at")
    fields = ("status", *readonly_fields)
    inlines = [TicketReplyInline]

    def has_add_permission(self, request):
        return False

    def save_formset(self, request, form, formset, change):
        """Replies typed in the admin are marked as staff replies and signed by the staff member."""
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj in instances:
            if isinstance(obj, TicketReply) and obj.pk is None:
                obj.author = request.user
                obj.is_staff_reply = True
            obj.save()
        formset.save_m2m()
