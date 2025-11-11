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
CODE_OWNER_BONUS = 100   # CODE OWNER
NEW_USER_BONUS = 50  # NEW USER
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
        new_user_profile = request.user.profile
        if new_user_profile.referred_by or raw_code == new_user_profile.referral_code:
            return Response({"message": "Referral processed successfully"})

        try:
            code_owner = UserProfile.objects.get(referral_code=raw_code)
        except UserProfile.DoesNotExist:
            return Response({"message": "Referral processed successfully"})

        # ALWAYS NO CHECKS
        new_user_profile.referred_by = code_owner

        code_owner_rewarded = False
        with transaction.atomic():
            # LOCK THE CODE OWNER & GIVE BONUS IF < LIMIT & SET REWARDED TO TRUE
            code_owner_locked = UserProfile.objects.select_for_update().get(id=code_owner.id)
            if code_owner_locked.total_referrals < REFERRALS_LIMIT:
                updated = UserProfile.objects.filter(
                    id=code_owner.id, total_referrals__lt=REFERRALS_LIMIT
                ).update(total_referrals=F('total_referrals') + 1)

                # THE > 0 CHECK IS BECAUSE THERE IS MOAL LEVEL VALIDATION FOR COIN
                # INCREMENTS THAT CANT BE 0 MUST BE POSITIVE INTEGERS
                if updated and CODE_OWNER_BONUS > 0:
                    code_owner_locked.user.get_wallet().increment_coins(CODE_OWNER_BONUS)
                    code_owner_rewarded = True

        # GIVE BONUS TO THE NEW USER IF THE REFERRER WAS REWARDED
        if code_owner_rewarded and NEW_USER_BONUS > 0:
            new_user_profile.user.get_wallet().increment_coins(NEW_USER_BONUS)

        new_user_profile.save()
        return Response({"message": "Referral processed successfully"})
