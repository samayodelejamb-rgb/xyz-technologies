from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse

from .emailing import deliver_contact_email
from .models import (
    ContactMessage, Milestone, Product, Project, Service, SiteSettings,
    Stat, TeamMember, Testimonial, Value,
)

admin.site.site_header = "XYZ Technologies administration"
admin.site.site_title = "XYZ admin"
admin.site.index_title = "Manage your website"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Company", {"fields": ("company_name", "tagline")}),
        ("Home page banner", {"fields": ("hero_title", "hero_text")}),
        ("About page", {"fields": ("about_intro", "mission", "vision")}),
        ("Contact details", {"fields": ("phone", "email", "address", "hours_weekdays", "hours_saturday", "map_embed_url")}),
        ("Social media", {"fields": ("facebook_url", "instagram_url", "linkedin_url", "x_url")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:website_sitesettings_change", args=[obj.pk]))


def register_orderable(model, columns, search):
    class Admin(admin.ModelAdmin):
        list_display = (*columns, "order", "is_published")
        list_display_links = (columns[0],)
        list_editable = ("order", "is_published")
        search_fields = search

    admin.site.register(model, Admin)


register_orderable(Stat, ("value", "label"), ("label",))
register_orderable(Service, ("title", "icon"), ("title", "summary"))
register_orderable(Product, ("name", "category"), ("name", "summary"))
register_orderable(Project, ("title", "sector"), ("title", "summary"))
register_orderable(Testimonial, ("author", "role"), ("author", "quote"))
register_orderable(TeamMember, ("name", "role"), ("name", "role"))
register_orderable(Value, ("title", "text"), ("title",))
register_orderable(Milestone, ("title", "year"), ("title", "text"))


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "email", "topic", "status", "email_sent")
    list_filter = ("status", "topic", "email_sent", "created_at")
    search_fields = ("name", "email", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("name", "email", "phone", "topic", "message", "created_at", "ip",
                       "user_agent", "email_sent", "email_error")
    fields = ("status", *readonly_fields)
    actions = ["mark_read", "mark_replied", "resend_email"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, queryset):
        queryset.update(status=ContactMessage.READ)

    @admin.action(description="Mark selected as replied")
    def mark_replied(self, request, queryset):
        queryset.update(status=ContactMessage.REPLIED)

    @admin.action(description="Resend notification email")
    def resend_email(self, request, queryset):
        sent = sum(1 for item in queryset if deliver_contact_email(item.pk))
        failed = queryset.count() - sent
        if sent:
            self.message_user(request, f"{sent} email(s) sent.", messages.SUCCESS)
        if failed:
            self.message_user(request, f"{failed} email(s) failed. Open the message to see the error.", messages.ERROR)
