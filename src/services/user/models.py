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