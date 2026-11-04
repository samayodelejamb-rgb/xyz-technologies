from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("services/", views.ServicesView.as_view(), name="services"),
    path("products/", views.ProductsView.as_view(), name="products"),
    path("projects/", views.ProjectsView.as_view(), name="projects"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("contact/send/", views.contact_send, name="contact_send"),
    path("healthz/", views.healthz, name="healthz"),
    path("robots.txt", views.robots_txt, name="robots"),
]
