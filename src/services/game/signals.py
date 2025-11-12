from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from .models import GameHistory



@receiver(post_save, sender=GameHistory)
def award_game_points(sender, instance, created, **kwargs):
    """
    On every new COMPLETED game:
    → Add calculated_points to UserProfile.total_game_points
    → Atomic update (no race conditions)
    """
    if not created or instance.status != sender.Status.COMPLETED:
        return

    points = instance.calculated_points

    with transaction.atomic():
        from src.services.user.models import UserProfile
        UserProfile.objects.filter(user=instance.player).update(
            total_game_points=F("total_game_points") + points
        )