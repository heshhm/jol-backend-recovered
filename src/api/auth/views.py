from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, SocialConnectView
from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.views import LoginView
from django.contrib.auth import authenticate
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from core.settings import GOOGLE_CALLBACK_ADDRESS, APPLE_CALLBACK_ADDRESS
from src.api.auth.serializer import PasswordSerializer

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
    """
    Custom login view that regenerates token on successful login. Deletes the old token
    and creates a new one to enhance security. and no multiple active tokens exist for a user -> no multiple devices at a time.
    """
    serializer_class = LoginSerializer

    def get_response(self):
        user = self.user  # set during serializer validation
        Token.objects.filter(user=user).delete()
        new_token = Token.objects.create(user=user)

        response = super().get_response()
        response.data['key'] = new_token.key
        return response


class DeactivateUserAPIView(APIView):
    """ Deactivate user account """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordSerializer

    def _validate_password(self, request):
        """ Validate the user's password """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        return request.user if request.user.check_password(password) else None

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
