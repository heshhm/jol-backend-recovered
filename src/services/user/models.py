import shortuuid
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F
from django_resized import ResizedImageField

def user_avatar_path(instance, filename):
    ext = filename.split(".")[-1]
    return f"avatars/{uuid.uuid4()}/{uuid.uuid4()}.{ext}"

class User(AbstractUser):
    email = models.EmailField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip() if self.email else self.email
        super().save(*args, **kwargs)

    def get_wallet(self):
        wallet, _ = UserWallet.objects.get_or_create(user=self)
        return wallet

    def __str__(self):
        return self.email or self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = ResizedImageField(
        size=[300, 300], crop=['middle', 'center'], quality=85,
        force_format="JPEG", upload_to=user_avatar_path,
        null=True, blank=True
    )


    # REFERRALS
    referral_code = models.CharField(max_length=8, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='referrals', db_index=True
    )
    total_referrals = models.PositiveIntegerField(default=0)

    # GAME POINTS
    total_game_points = models.PositiveBigIntegerField(
        default=0,
        db_index=True,
        help_text="Total points earned from completed games"
    )
    used_game_points = models.PositiveBigIntegerField(
        default=0,
        help_text="Points redeemed for rewards"
    )

    @property
    def available_game_points(self):
        return self.total_game_points - self.used_game_points

    @property
    def referral_link(self):
        """
        Returns the full shareable referral link using query parameter style.
        Example: https://yourdomain.com/download?refcode=ABC123
        """
        from django.conf import settings
        code = self.referral_code or ''
        return f"https://nonabstemiously-stocky-cynthia.ngrok-free.dev/download?refcode={code}"
        # TODO: FIX THIS
        # return f"{settings.BASE_URL}/download?refcode={code}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        for _ in range(10):
            code = shortuuid.ShortUUID(
                alphabet="23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
            ).random(length=6)
            if not UserProfile.objects.filter(referral_code=code).exists():
                return code
        return shortuuid.uuid()[:8].upper()

    def __str__(self):
        return f"Profile of {self.user}"


class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    total_coins = models.PositiveIntegerField(default=0)
    used_coins = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_coins(self):
        return self.total_coins - self.used_coins

    def increment_coins(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        updated = UserWallet.objects.filter(user=self.user).update(
            total_coins=F('total_coins') + amount
        )
        if updated:
            self.refresh_from_db()
        return updated

    def decrement_coins(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        updated = UserWallet.objects.filter(
            user=self.user,
            total_coins__gte=F('used_coins') + amount
        ).update(
            used_coins=F('used_coins') + amount
        )
        if not updated:
            raise ValueError("Insufficient coins")
        self.refresh_from_db()
        return True

    def __str__(self):
        return f"{self.user} – {self.available_coins} coins"


class PendingReferral(models.Model):
    """
    Tracks a potential referral when a visitor clicks a shared referral link.
    Created when a visitor clicks a download button and includes the referral code
    and the visitor's public IP address. Later matched at signup time.
    """
    referral_code = models.CharField(max_length=50, db_index=True)
    referrer_profile = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='pending_referrals',
        help_text="The user profile that owns this referral code"
    )
    ip_address = models.GenericIPAddressField(db_index=True, help_text="IPv4 or IPv6 address")
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Redemption tracking
    redeemed_at = models.DateTimeField(null=True, blank=True)
    redeemed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='redeemed_referrals',
        help_text="User who signed up using this referral"
    )

    class Meta:
        verbose_name = "Pending Referral"
        verbose_name_plural = "Pending Referrals"
        indexes = [
            models.Index(fields=['ip_address', 'redeemed_at']),
            models.Index(fields=['referral_code', 'clicked_at']),
        ]
        ordering = ['-clicked_at']

    def __str__(self):
        status = "Redeemed" if self.redeemed_at else "Pending"
        return f"{self.referral_code} - {self.ip_address} ({status})"

    def is_redeemed(self):
        return self.redeemed_at is not None