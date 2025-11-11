from rest_framework import permissions, status
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from src.services.user.models import UserProfile

REFERRAL_BONUS = 100  # [heshhm] move this to commons model for easier access post launch

from src.api.v1.user.serializers import CoinSerializer, UserSerializer


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
        referral_code = request.data.get("referral_code")
        profile = request.user.profile

        # If user already has referred_by, ignore [ this should not be handled like this ]
        if profile.referred_by or not referral_code:
            return Response({"message": "Referral processed"}, status=status.HTTP_200_OK)

        try:
            referrer = UserProfile.objects.get(referral_code=referral_code)
        except UserProfile.DoesNotExist:
            # Invalid code → Tell the user but no error emitted
            return Response({"message": "Provided Code is wrong please re-check"}, status=status.HTTP_200_OK)

        # Assign referred_by
        profile.referred_by = referrer
        profile.save()

        # Reward coins
        referrer.user.get_wallet().increment_coins(REFERRAL_BONUS)

        # Increment referrer's total referrals
        referrer.total_referrals += 1
        referrer.save()

        return Response({"message": "Referral processed"}, status=status.HTTP_200_OK)
