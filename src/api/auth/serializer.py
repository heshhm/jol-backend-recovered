from rest_framework import serializers

class PasswordSerializer(serializers.Serializer):
    """
    Serializes the password for user authentication.
    The password field is required and write-only.
    """
    password = serializers.CharField(required=True, write_only=True)
