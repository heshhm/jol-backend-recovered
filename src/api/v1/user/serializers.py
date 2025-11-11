from rest_framework import serializers

from src.services.user.models import User, UserWallet, UserProfile

class CoinSerializer(serializers.Serializer):
    """
    Serializes the coin data for user wallet updates.
    The coins field is required and must be an integer.
    """
    coins = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=['increment', 'decrement'], required=True)


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


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'birth_date', 'avatar',
            'referral_code', 'referred_by', 'total_referrals'
        ]
        read_only_fields = ['referral_code', 'total_referrals']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes user data for API responses.
    Includes fields for primary key, email, username, first name, and last name.
    The primary key and email are read-only.
    """
    wallet = UserWalletSerializer(read_only=True, source='get_wallet')
    profile = UserProfileSerializer(read_only=True)  # <-- nested profile serializer

    class Meta:
        model = User
        fields = [
            'pk', 'email', 'username', 'first_name', 'last_name', 'wallet', 'profile'
        ]
        read_only_fields = ['pk', 'email']