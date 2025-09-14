from rest_framework import serializers
from src.services.users.models import User
from src.services.wallet.models import Wallet


class UserWalletSerializer(serializers.ModelSerializer):
    """
    Serializes user wallet data for API responses.
    Includes fields for total coins, used coins, and available coins.
    All fields are read-only.
    """

    class Meta:
        model = Wallet
        fields = [
            'total_coins', 'used_coins', 'available_coins'
        ]


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


class PasswordSerializer(serializers.Serializer):
    """
    Serializes the password for user authentication.
    The password field is required and write-only.
    """
    password = serializers.CharField(required=True, write_only=True)


class CoinSerializer(serializers.Serializer):
    """
    Serializes the coin data for user wallet updates.
    The coins field is required and must be an integer.
    """
    coins = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=['increment', 'decrement'], required=True)
