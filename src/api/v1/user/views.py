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
from src.api.v1.user.serializers import RedeemSerializer

# TODO: [heshhm] move this to commons model for easier access post launch
CODE_OWNER_BONUS = 100   # CODE OWNER
NEW_USER_BONUS = 50  # NEW USER
REFERRALS_LIMIT = 7
# Number of game points required to produce 1 coin
# e.g. COIN_VALUE = 100 means 100 points -> 1 coin
COIN_VALUE = 100

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
        """
        Prefer IP-based attribution. Flow:
        - If user already has referred_by, do nothing.
        - Try to find an unredeemed PendingReferral by the request IP.
        - If found, use the referrer_profile FK directly; otherwise, fall back to explicit referral_code in body.
        - Prevent self-referral and duplicate processing.
        - Atomically mark PendingReferral redeemed, increment referrer's total_referrals and coins,
          and credit new user if applicable.
        """
        from src.commons.utils import get_client_ip
        from src.services.user.models import PendingReferral
        from django.utils import timezone

        user_id = request.user.id
        print(f"\n>>> [REF] Starting referral process for User ID: {user_id}")

        new_user_profile = request.user.profile

        # If already referred, nothing to do
        if new_user_profile.referred_by:
            print(f">>> [REF] User {user_id} already has referrer: {new_user_profile.referred_by.id}. Aborting.")
            return Response({"message": "Referral processed successfully"})

        # Try IP-based lookup first
        client_ip = get_client_ip(request)
        print(f">>> [REF] Client IP detected: {client_ip}")

        pending = None
        code_owner = None
        attributed_via = None

        if client_ip:
            pending = PendingReferral.objects.select_related('referrer_profile').filter(
                ip_address=client_ip,
                redeemed_at__isnull=True
            ).order_by('-clicked_at').first()

        if pending:
            # Use the FK directly — no lookup needed
            code_owner = pending.referrer_profile
            attributed_via = 'ip'
            print(f">>> [REF] Found PendingReferral via IP. ID: {pending.id}, Referrer: {code_owner.user_id}")
        else:
            # Fallback: explicit referral_code in body
            raw_code = request.data.get('referral_code', '').strip().upper()
            print(f">>> [REF] No IP match. Attempting manual code: '{raw_code}'")

            if raw_code:
                try:
                    code_owner = UserProfile.objects.get(referral_code=raw_code)
                    attributed_via = 'code'
                    print(f">>> [REF] Manual code owner found. Owner User ID: {code_owner.user_id}")
                except UserProfile.DoesNotExist:
                    print(f">>> [REF] Manual code '{raw_code}' does not exist in DB.")

        if not code_owner:
            print(">>> [REF] No referral code present (neither IP nor manual). Exiting.")
            return Response({"message": "Referral processed successfully"})

        # Prevent self-referral
        if code_owner.id == new_user_profile.id:
            print(f">>> [REF] Self-referral detected for user {user_id}. Aborting.")
            return Response({"message": "Referral processed successfully"})

        # Atomic update: credit referrer (if under limit) and mark pending as redeemed
        code_owner_rewarded = False
        print(">>> [REF] Entering atomic transaction block...")

        try:
            with transaction.atomic():
                code_owner_locked = UserProfile.objects.select_for_update().get(id=code_owner.id)
                print(f">>> [REF] Locked owner profile. Current referrals: {code_owner_locked.total_referrals}")

                # Give referrer bonus if still under limit
                if code_owner_locked.total_referrals < REFERRALS_LIMIT:
                    updated = UserProfile.objects.filter(
                        id=code_owner.id, total_referrals__lt=REFERRALS_LIMIT
                    ).update(total_referrals=F('total_referrals') + 1)

                    if updated and CODE_OWNER_BONUS > 0:
                        code_owner_locked.user.get_wallet().increment_coins(CODE_OWNER_BONUS)
                        code_owner_rewarded = True
                        print(f">>> [REF] Owner credited with bonus: {CODE_OWNER_BONUS}")
                else:
                    print(f">>> [REF] Owner hit referral limit ({REFERRALS_LIMIT}). No bonus given.")

                # Set referred_by on new user's profile
                new_profile_locked = UserProfile.objects.select_for_update().get(id=new_user_profile.id)
                new_profile_locked.referred_by = code_owner_locked
                new_profile_locked.save()
                print(f">>> [REF] Linked new user {user_id} to referrer {code_owner_locked.id}")

                # If we matched via pending referral, mark it redeemed
                if pending:
                    pending.redeemed_at = timezone.now()
                    pending.redeemed_by = request.user
                    pending.save()
                    print(f">>> [REF] PendingReferral {pending.id} marked as redeemed.")

            # Give bonus to new user only if referrer was rewarded
            if code_owner_rewarded and NEW_USER_BONUS > 0:
                request.user.get_wallet().increment_coins(NEW_USER_BONUS)
                print(f">>> [REF] New user {user_id} credited with join bonus: {NEW_USER_BONUS}")

            print(">>> [REF] Referral process completed successfully.")
            return Response({"message": "Referral processed successfully", "attributed_via": attributed_via})

        except Exception as e:
            print(f">>> [REF] ERROR: Referral process failed for user {user_id}: {e}")
            return Response({"error": "Referral processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ErrorTestAPIView(APIView):
    """
    An endpoint to deliberately raise an exception for testing error logging.
    GET /v1/error/test/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        raise Exception("Deliberate exception for testing error logging middleware.")


class RedeemPointsAPIView(APIView):
    """
    Redeem game points into coins.

    POST /v1/wallet/redeem/
    Body: { "coins": <int> }

    Validation & behavior:
    - Verifies user has enough available_game_points to cover coins * COIN_VALUE
    - Atomically increments wallet.total_coins and increments profile.used_game_points
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coins = serializer.validated_data['coins']

        points_required = coins * COIN_VALUE

        from src.services.user.models import UserProfile, UserWallet
        from django.db import transaction
        from django.db.models import F

        # Ensure wallet exists (get_or_create) before locking
        request.user.get_wallet()

        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=request.user)
            wallet = UserWallet.objects.select_for_update().get(user=request.user)

            available = profile.total_game_points - profile.used_game_points
            if available < points_required:
                return Response({"error": "Insufficient game points"}, status=status.HTTP_400_BAD_REQUEST)

            # Apply updates atomically using F expressions
            UserProfile.objects.filter(user=request.user).update(
                used_game_points=F('used_game_points') + points_required
            )
            UserWallet.objects.filter(user=request.user).update(
                total_coins=F('total_coins') + coins
            )

            # Refresh instances for response
            profile.refresh_from_db()
            wallet.refresh_from_db()

        return Response({
            "coins_awarded": coins,
            "available_game_points": profile.total_game_points - profile.used_game_points,
            "available_coins": wallet.total_coins - wallet.used_coins,
        })