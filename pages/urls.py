from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("terms/", views.TermsView.as_view(), name="terms"),
]
