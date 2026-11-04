from django.db import DatabaseError

from .models import SiteSettings

NAV = [
    ("home", "Home"),
    ("about", "About"),
    ("services", "Services"),
    ("products", "Products"),
    ("projects", "Projects"),
    ("contact", "Contact"),
]


def site(request):
    """Makes company details and the menu available in every template."""
    try:
        settings_obj = SiteSettings.load()
    except DatabaseError:  # tables not created yet (before 'migrate')
        settings_obj = SiteSettings()
    return {"site": settings_obj, "nav": NAV}
