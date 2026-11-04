from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return ["home", "about", "services", "products", "projects", "contact"]

    def location(self, item):
        return reverse(item)
