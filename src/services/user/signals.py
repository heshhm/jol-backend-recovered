from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserWallet

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        UserWallet.objects.create(user=instance)
