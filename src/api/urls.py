from django.urls import path, include
from .schema import schema_urls

urlpatterns = [
    path("auth/", include("src.api.auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),

    path("v1/", include("src.api.v1.urls")),
] + schema_urls