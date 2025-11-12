from django.urls import path, include

urlpatterns = [
    path('user/', include('src.api.v1.user.urls')),
    path('game/', include('src.api.v1.game.urls'))
]
