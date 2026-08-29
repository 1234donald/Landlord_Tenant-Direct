"""Root URL configuration for the REST API."""
from django.urls import include, path

urlpatterns = [
    path("v1/", include("api.v1.urls")),
]
