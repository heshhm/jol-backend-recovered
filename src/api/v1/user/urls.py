from .views import UserWalletUpdateAPIView, UserRetrieveChangeAPIView, ProcessReferralAPIView
from django.urls import path

urlpatterns = [
    path('profile/', UserRetrieveChangeAPIView.as_view(), name='user_retrieve_update'),

    path('wallet-update/', UserWalletUpdateAPIView.as_view(), name='wallet_update'),

    path("process-referral/", ProcessReferralAPIView.as_view(), name="process-referral"),
]