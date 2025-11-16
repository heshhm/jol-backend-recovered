from rest_framework import serializers
from src.services.user.models import User, UserWallet, UserProfile

class CoinSerializer(serializers.Serializer):
    """
    Serializes the coin data for user wallet updates.
    'coins' is required and must be an integer.
    'type' is required and must be either 'increment' or 'decrement'.
    """
    coins = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=['increment', 'decrement'], required=True)


class RedeemSerializer(serializers.Serializer):
    """
    Serializer for redeeming game points into coins.
    Request body: { "coins": <int> }
    """
    coins = serializers.IntegerField(min_value=1, required=True)


class UserWalletSerializer(serializers.ModelSerializer):
    """
    Serializes user wallet data for API responses.
    Includes fields for total coins, used coins, and available coins.
    All fields are read-only.
    """
    class Meta:
        model = UserWallet
        fields = ['total_coins', 'used_coins', 'available_coins']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializes the full user profile data for read operations.
    Includes bio, location, birth_date, avatar, referral code,
    referred_by, and total_referrals.
    """
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'birth_date', 'avatar',
            'referral_code', 'referred_by', 'total_referrals'
        ]
        read_only_fields = ['referral_code', 'total_referrals']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile fields.
    Allows only editable fields: bio, location, birth_date, avatar.
    """
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birth_date', 'avatar']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes user account data for API responses.
    Includes first_name, last_name, email, username, wallet summary, and nested profile.
    'pk' and 'email' are read-only.
    """


    class Meta:
        model = User
        fields = ['pk', 'email', 'username', 'first_name', 'last_name']
        read_only_fields = ['pk', 'email']
