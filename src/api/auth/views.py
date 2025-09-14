from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, SocialConnectView
from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.views import LoginView
from django.contrib.auth import authenticate
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.settings import GOOGLE_CALLBACK_ADDRESS, APPLE_CALLBACK_ADDRESS
from src.api.auth.serializer import PasswordSerializer, UserSerializer, CoinSerializer


class GoogleLogin(SocialLoginView):
    """ Handles Google social login """
    adapter_class = GoogleOAuth2Adapter
    callback_url = GOOGLE_CALLBACK_ADDRESS
    client_class = OAuth2Client


class GoogleConnect(SocialConnectView):
    """ Handles Google social account connection """
    adapter_class = GoogleOAuth2Adapter
    callback_url = GOOGLE_CALLBACK_ADDRESS
    client_class = OAuth2Client


class AppleLogin(SocialLoginView):
    """ Handles Apple social login """
    adapter_class = AppleOAuth2Adapter
    callback_url = APPLE_CALLBACK_ADDRESS
    client_class = OAuth2Client


class AppleConnect(SocialConnectView):
    """ Handles Apple social account connection """
    adapter_class = AppleOAuth2Adapter
    callback_url = APPLE_CALLBACK_ADDRESS
    client_class = OAuth2Client


class CustomLoginView(LoginView):
    """ Custom login view that generates a new auth token for the user """
    serializer_class = LoginSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if request.user.is_authenticated:
            user = request.user
            Token.objects.filter(user=user).delete()
            new_token = Token.objects.create(user=user)
            response.data['key'] = new_token.key
        return response


class UserRetrieveChangeAPIView(RetrieveUpdateAPIView):
    """ Retrieve and update user account information """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """ Get the current authenticated user """
        return self.request.user


class UserWalletUpdateAPIView(GenericAPIView):
    """ Increment or decrement user wallet coins
    CHOICES = (
        ('increment', 'Increment'),
        ('decrement', 'Decrement'),
    )
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoinSerializer

    def post(self, request, *args, **kwargs):
        coins = request.data.get('coins')
        coin_type = request.data.get('type')
        user_wallet = request.user.get_wallet()
        if coin_type == 'increment':
            user_wallet.total_coins += coins
            user_wallet.available_coins += coins
            user_wallet.save()
            return Response(
                data={'message': 'Coins added successfully'},
                status=status.HTTP_200_OK
            )
        elif coin_type == 'decrement':
            if user_wallet.available_coins < coins:
                return Response(
                    data={'error': 'Insufficient coins'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user_wallet.available_coins -= coins
            user_wallet.used_coins += coins
            user_wallet.save()
            return Response(
                data={'message': 'Coins deducted successfully'},
                status=status.HTTP_200_OK
            )
        return Response(
            data={'error': 'Invalid coin type'},
            status=status.HTTP_400_BAD_REQUEST
        )


class DeactivateUserAPIView(APIView):
    """ Deactivate user account """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordSerializer

    def _validate_password(self, request):
        """ Validate the user's password """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        user = authenticate(email=request.user.email, password=password)
        return user

    def post(self, request, *args, **kwargs):
        user = self._validate_password(request)
        if user is None:
            return Response(
                data={'error': 'Enter a Valid Password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deactivate the user account
        request.user.is_active = False
        request.user.save()

        return Response(
            data={'message': 'User account has been deactivated'},
            status=status.HTTP_200_OK
        )


class DeleteUserAPIView(APIView):
    """ Delete user account """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordSerializer

    def _validate_password(self, request):
        """ Validate the user's password """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        user = authenticate(email=request.user.email, password=password)
        return user

    def post(self, request, *args, **kwargs):
        user = self._validate_password(request)
        if user is None:
            return Response(
                data={'error': 'Enter a Valid Password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.delete()

        return Response(
            data={'message': 'User account has been deleted'},
            status=status.HTTP_200_OK
        )
