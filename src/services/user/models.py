from django.contrib.auth.models import AbstractUser
from django.db import models


from django_resized import ResizedImageField
import os
import uuid


class User(AbstractUser):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def user_avatar_path(instance, filename):
    ext = filename.split(".")[-1]
    return f"auth_user_avatar/{instance.id}/{uuid.uuid4()}.{ext}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

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

    def __str__(self):
        return f"Profile of {self.user.username}"
