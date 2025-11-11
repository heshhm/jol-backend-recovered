from rest_framework import permissions, status
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db import transaction
from django.db.models import F

from src.services.user.models import UserProfile
from src.api.v1.user.serializers import CoinSerializer, UserSerializer

# [heshhm] move this to commons model for easier access post launch
REFERRAL_BONUS_REFERRER = 100   # THE PERSON WHO REFERS IE THE REFERRAL CODE OWNER
REFERRAL_BONUS_REFEREE = 0  # THE PERSON BEING REFERRED IE THE NEW USER
REFERRALS_LIMIT = 8


class UserWalletUpdateAPIView(GenericAPIView):
    """ Increment or decrement user wallet coins
    CHOICES = (
        ('increment', 'Increment'),
        ('decrement', 'Decrement'),
    )
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoinSerializer

    #noinspection PyMethodMayBeStatic
    def post(self, request, *args, **kwargs):
        coins = request.data.get('coins')
        coin_type = request.data.get('type')
        user_wallet = request.user.get_wallet()

        try:
            if coin_type == 'increment':
                user_wallet.increment_coins(coins)
                return Response(
                    data={'message': 'Coins added successfully'},
                    status=status.HTTP_200_OK
                )
            elif coin_type == 'decrement':
                user_wallet.decrement_coins(coins)
                return Response(
                    data={'message': 'Coins deducted successfully'},
                    status=status.HTTP_200_OK
                )
            return Response(
                data={'error': 'Invalid coin type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserRetrieveChangeAPIView(RetrieveUpdateAPIView):
    """ Retrieve and update user account information """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """ Get the current authenticated user """
        return self.request.user


class ProcessReferralAPIView(APIView):
    """
    Called after onboarding when a user provides a referral code.
    request.user is the new user being referred.
    """
    def post(self, request):
        raw_code = request.data.get("referral_code", "").strip().upper()
        if not raw_code:
            return Response({"message": "Referral processed successfully"}, status=status.HTTP_200_OK)

        profile = request.user.profile
        if profile.referred_by:
            return Response({"message": "Referral processed successfully"}, status=status.HTTP_200_OK)

        try:
            referrer = UserProfile.objects.get(referral_code=raw_code)
        except UserProfile.DoesNotExist:
            return Response({"message": "Referral processed successfully"}, status=status.HTTP_200_OK)

        # Always track who referred them (for analytics)
        profile.referred_by = referrer

        referrer_rewarded = False
        with transaction.atomic():
            # Lock and check limit
            referrer_locked = UserProfile.objects.select_for_update().get(id=referrer.id)

            if referrer_locked.total_referrals < REFERRALS_LIMIT:
                updated = UserProfile.objects.filter(
                    id=referrer.id,
                    total_referrals__lt=REFERRALS_LIMIT
                ).update(total_referrals=F('total_referrals') + 1)

                if updated:
                    referrer_locked.user.get_wallet().increment_coins(REFERRAL_BONUS_REFERRER)
                    referrer_rewarded = True

        # Reward referee only if referrer was rewarded
        if referrer_rewarded:
            profile.user.get_wallet().increment_coins(REFERRAL_BONUS_REFEREE)

        profile.save()

        return Response({"message": "Referral processed successfully"}, status=status.HTTP_200_OK)
