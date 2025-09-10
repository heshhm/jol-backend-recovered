from django.urls import path, include, re_path

urlpatterns = [


    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),

]
