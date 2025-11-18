from src.commons.handlers import handler404, handler500
from src.commons.views import DownloadPageView
from core.settings import MEDIA_ROOT, STATIC_ROOT

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve


handler404 = handler404
handler500 = handler500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('src.api.urls')),

    path('accounts/', include('allauth.urls')),

    # Referral download page (referral_code is optional)
    path('download/', DownloadPageView.as_view(), name='download'),

    # TODO REMOVE DJ_ANALYTICS
    path("", include("django_analytics.urls")),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': STATIC_ROOT}),
]