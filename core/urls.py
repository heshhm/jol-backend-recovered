from src.commons.handlers import handler404, handler500
from src.commons.views import DownloadPageView, PasswordResetConfirmPageView
from core.settings import MEDIA_ROOT, STATIC_ROOT

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.views.generic import RedirectView


handler404 = handler404
handler500 = handler500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('src.api.urls')),

    path('accounts/', include('allauth.urls')),

    # Referral download page (referral_code is optional)
    path('download/', DownloadPageView.as_view(), name='download'),

    # Password reset – branded HTML page (email links land here)
    re_path(
        r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        PasswordResetConfirmPageView.as_view(),
        name='password_reset_confirm'
    ),

    # Redirect root to download page
    path('', RedirectView.as_view(url='/download/', permanent=False)),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': STATIC_ROOT}),
]