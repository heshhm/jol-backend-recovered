from .views import UserWalletUpdateAPIView, UserRetrieveChangeAPIView
from django.urls import path

urlpatterns = [
    path('profile/', UserRetrieveChangeAPIView.as_view(), name='user_retrieve_update'),
    path('wallet-update/', UserWalletUpdateAPIView.as_view(), name='wallet_update'),
]