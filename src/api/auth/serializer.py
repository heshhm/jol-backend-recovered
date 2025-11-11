from rest_framework import serializers
from src.services.user.models import User

# THE USER SERIALIZER JUST IN CASE
from src.api.v1.user.serializers import UserSerializer


class PasswordSerializer(serializers.Serializer):
    """
    Serializes the password for user authentication.
    The password field is required and write-only.
    """
    password = serializers.CharField(required=True, write_only=True)
