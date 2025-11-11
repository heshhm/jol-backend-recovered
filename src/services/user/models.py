import random, string
from django.contrib.auth.models import AbstractUser
from django.db import models


from django_resized import ResizedImageField
import os
import uuid

def user_avatar_path(instance, filename):
    ext = filename.split(".")[-1]
    return f"auth_user_avatar/{instance.id}/{uuid.uuid4()}.{ext}"


class User(AbstractUser):
    email = models.EmailField(unique=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_wallet(self):
        """
        This is just being safe, wallet should be created on user creation via signals.
        """
        wallet, _ = UserWallet.objects.get_or_create(user=self)
        return wallet


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # --- Referral fields ---
    referral_code = models.CharField(max_length=6, unique=True, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    total_referrals = models.PositiveIntegerField(default=0)

    avatar = ResizedImageField(
        size=[300, 300],
        crop=['middle', 'center'],
        quality=85,
        keep_meta=False,
        force_format="JPEG",
        upload_to=user_avatar_path,
        null=True,
        blank=True,
    )


    def save(self, *args, **kwargs):
        """
        Override save method to generate referral code if not present.
        """
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def generate_referral_code(self):
        """Generate a unique 6-character alphanumeric code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not UserProfile.objects.filter(referral_code=code).exists():
                return code

    def __str__(self):
        return f"Profile of {self.user.username}"


class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')

    total_coins = models.IntegerField(default=0)
    used_coins = models.IntegerField(default=0)
    available_coins = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.username}"

    def increment_coins(self, amount):
        self.total_coins += amount
        self.available_coins += amount
        self.save()

    def decrement_coins(self, amount):
        if amount > self.available_coins:
            raise ValueError("Insufficient available coins")
        self.used_coins += amount
        self.available_coins -= amount
        self.save()