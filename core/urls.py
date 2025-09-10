from src.commons.handlers import handler404, handler500

from django.contrib import admin
from django.urls import path, include

handler404 = handler404
handler500 = handler500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.v1.urls')),
]
