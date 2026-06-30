from django.urls import path

from . import views

app_name = "animals"

urlpatterns = [
    path("", views.MyAnimalsView.as_view(), name="list"),
    # Animals
    path("new/", views.AnimalCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AnimalDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.AnimalUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.AnimalDeleteView.as_view(), name="delete"),
    # Herds
    path("herds/new/", views.HerdCreateView.as_view(), name="herd_create"),
    path("herds/<int:pk>/", views.HerdDetailView.as_view(), name="herd_detail"),
    path("herds/<int:pk>/edit/", views.HerdUpdateView.as_view(), name="herd_update"),
    path("herds/<int:pk>/delete/", views.HerdDeleteView.as_view(), name="herd_delete"),
]
