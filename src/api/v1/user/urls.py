from django.urls import path
from .views import (
    UserRetrieveUpdateAPIView,
    UserProfileRetrieveUpdateAPIView,
    UserWalletAPIView,
    UserWalletUpdateAPIView,
    ProcessReferralAPIView, ErrorTestAPIView,
    RedeemPointsAPIView,
)

app_name = 'user'
urlpatterns = [
    path( 'detail/', UserRetrieveUpdateAPIView.as_view(), name='user_retrieve_update'),
    path( 'profile/', UserProfileRetrieveUpdateAPIView.as_view(), name='user_profile_retrieve_update'),
    path( 'wallet/', UserWalletAPIView.as_view(), name='user_wallet_retrieve' ),

    path( 'wallet/adjust/', UserWalletUpdateAPIView.as_view(), name='user_wallet_update'),
    path( 'wallet/redeem/', RedeemPointsAPIView.as_view(), name='user_wallet_redeem'),
    path( 'process-referral/',  ProcessReferralAPIView.as_view(), name='process_referral'),

    path( 'error/test/',  ErrorTestAPIView.as_view(), name='error_test'),
]
