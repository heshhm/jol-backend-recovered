from django.urls import path, include

urlpatterns = [
    path('user/', include('src.api.v1.user.urls'))
]
