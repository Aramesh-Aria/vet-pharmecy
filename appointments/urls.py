from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("request/", views.request_appointment, name="request"),
    path("", views.AppointmentListView.as_view(), name="list"),
    path("<int:pk>/", views.AppointmentDetailView.as_view(), name="detail"),
    path("<int:pk>/cancel/", views.cancel_appointment, name="cancel"),
]
