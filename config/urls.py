from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from website.sitemaps import StaticViewSitemap

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": {"pages": StaticViewSitemap}}, name="sitemap"),
    path("account/", include("accounts.urls")),
    path("", include("website.urls")),
]
