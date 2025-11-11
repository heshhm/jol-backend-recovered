from allauth.account import app_settings as allauth_account_settings
from allauth.account.adapter import get_adapter
from allauth.utils import email_address_exists
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes user data for API responses.
    Includes fields for primary key, email, username, first name, and last name.
    The primary key and email are read-only.
    """
    wallet = UserWalletSerializer(read_only=True, source='get_wallet')

    class Meta:
        model = User
        fields = [
            'pk', 'email', 'username', 'first_name', 'last_name', 'wallet'
        ]
        read_only_fields = ['pk', 'email']

class UserWalletSerializer(serializers.ModelSerializer):
    """
    Serializes user wallet data for API responses.
    Includes fields for total coins, used coins, and available coins.
    All fields are read-only.
    """

    class Meta:
        model = UserWallet
        fields = [
            'total_coins', 'used_coins', 'available_coins'
        ]

class CustomRegisterSerializer(RegisterSerializer):
    """
    Custom registration serializer that works with the new allauth API
    (ACCOUNT_SIGNUP_FIELDS) instead of deprecated settings.
    """

    email = serializers.EmailField(
        required=allauth_account_settings.SIGNUP_FIELDS["email"]["required"]
    )
    username = serializers.CharField(
        required=allauth_account_settings.SIGNUP_FIELDS["username"]["required"]
    )

    def validate_email(self, email):
        """
        Ensure email uniqueness if ACCOUNT_UNIQUE_EMAIL = True.
        """
        email = get_adapter().clean_email(email)
        if allauth_account_settings.UNIQUE_EMAIL and email_address_exists(email):
            raise serializers.ValidationError("A user is already registered with this e-mail address.")
        return email

    def validate_username(self, username):
        """
        Use allauth's username validation.
        """
        return get_adapter().clean_username(username)

    def get_cleaned_data(self):
        """
        What data actually gets passed to create_user().
        """
        return {
            "username": self.validated_data.get("username", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
            "email": self.validated_data.get("email", ""),
        }

class CoinSerializer(serializers.Serializer):
    """
    Serializes the coin data for user wallet updates.
    The coins field is required and must be an integer.
    """
    coins = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=['increment', 'decrement'], required=True)
