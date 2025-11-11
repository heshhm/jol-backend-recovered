from rest_framework import permissions, status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db import transaction
from django.db.models import F

from src.services.user.models import UserProfile
from src.api.v1.user.serializers import (
    CoinSerializer, UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer, UserWalletSerializer
)

# [heshhm] move this to commons model for easier access post launch
REFERRAL_BONUS_REFERRER = 100   # CODE OWNER
REFERRAL_BONUS_REFEREE = 50  # NEW USER
REFERRALS_LIMIT = 7

class UserWalletAPIView(APIView):
    """
    Retrieves the current authenticated user's wallet information.
    GET /v1/wallet/
    Returns total_coins, used_coins, and available_coins.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet = request.user.get_wallet()
        serializer = UserWalletSerializer(wallet)
        return Response(serializer.data)

class UserWalletUpdateAPIView(APIView):
    """
    Updates the authenticated user's wallet by incrementing or decrementing coins.
    POST /v1/wallet/adjust/
    Expects a JSON body with 'coins' (int) and 'type' ('increment'|'decrement').
    Validates coin type and handles insufficient balance errors.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoinSerializer

    def post(self, request):
        serializer = CoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coins = serializer.validated_data['coins']
        coin_type = serializer.validated_data['type']

        wallet = request.user.get_wallet()
        try:
            if coin_type == 'increment':
                wallet.increment_coins(coins)
                return Response({"message": "Coins added successfully"})
            elif coin_type == 'decrement':
                wallet.decrement_coins(coins)
                return Response({"message": "Coins deducted successfully"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Invalid coin type"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.
    GET /v1/profile/ - returns full profile data.
    PATCH /v1/profile/ - updates editable fields: bio, location, birth_date, avatar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user.profile


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's account information.
    GET /v1/user/ - returns username, email, names, wallet, and profile summary.
    PATCH /v1/user/ - updates first_name and last_name only.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class ProcessReferralAPIView(APIView):
    """
    Processes a referral code after user onboarding.
    POST /v1/referral/
    Rewards the referrer and referee based on predefined limits and bonus rules.
    Ensures a user cannot refer themselves or submit multiple referrals.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_code = request.data.get("referral_code", "").strip().upper()
        if not raw_code:
            return Response({"message": "Referral processed successfully"})

        # CHECK IF USER HAS ALREADY BEEN REFERRED OR IS USING THEIR OWN CODE
        # NIGGAS BE TRYNA CHEAT
        profile = request.user.profile
        if profile.referred_by or raw_code == profile.referral_code:
            return Response({"message": "Referral processed successfully"})

        try:
            referrer = UserProfile.objects.get(referral_code=raw_code)
        except UserProfile.DoesNotExist:
            return Response({"message": "Referral processed successfully"})

        profile.referred_by = referrer

        referrer_rewarded = False
        with transaction.atomic():
            # LOCK THE REFERRER & GIVE BONUS IF < LIMIT & SET REWARDED TO TRUE
            referrer_locked = UserProfile.objects.select_for_update().get(id=referrer.id)
            if referrer_locked.total_referrals < REFERRALS_LIMIT:
                updated = UserProfile.objects.filter(
                    id=referrer.id, total_referrals__lt=REFERRALS_LIMIT
                ).update(total_referrals=F('total_referrals') + 1)

                # THE > 0 CHECK IS BECAUSE THERE IS MOAL LEVEL VALIDATION FOR COIN
                # INCREMENTS THAT CANT BE 0 MUST BE POSITIVE INTEGERS
                if updated and REFERRAL_BONUS_REFERRER > 0:
                    referrer_locked.user.get_wallet().increment_coins(REFERRAL_BONUS_REFERRER)
                    referrer_rewarded = True

        # GIVE BONUS TO THE NEW USER IF THE REFERRER WAS REWARDED
        if referrer_rewarded and REFERRAL_BONUS_REFERRER > 0:
            profile.user.get_wallet().increment_coins(REFERRAL_BONUS_REFEREE)

        profile.save()
        return Response({"message": "Referral processed successfully"})
