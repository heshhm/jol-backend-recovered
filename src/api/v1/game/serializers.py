from rest_framework import serializers
from django.contrib.auth import get_user_model

from src.services.game.models import GameHistory

User = get_user_model()


class GameHistoryCreateSerializer(serializers.ModelSerializer):
    player_id = serializers.CharField(write_only=True)  # frontend sends it

    class Meta:
        model = GameHistory
        fields = [
            "match_id", "player_id",
            "game_type", "game_mode", "operation",
            "grid_size", "timestamp", "status",
            "final_score", "accuracy_percentage", "hints_used",
            "completion_time", "room_code", "position", "total_players"
        ]
        extra_kwargs = {
            "match_id": {"required": True},
            "completion_time": {"required": False},
            "room_code": {"required": False},
            "position": {"required": False},
            "total_players": {"required": False},
        }

    def validate_player_id(self, value):
        """Ensure player_id matches current user"""
        if str(self.context["request"].user.id) != value:
            raise serializers.ValidationError("player_id does not match authenticated user.")
        return value

    def validate(self, data):
        # Timed mode requires completion_time
        if data.get("game_mode") == "timed" and data.get("completion_time") is None:
            raise serializers.ValidationError({
                "completion_time": "Required for timed mode."
            })

        # Multiplayer requires these fields
        if data.get("game_type") == "multiplayer":
            missing = [
                f for f in ("room_code", "position", "total_players")
                if not data.get(f)
            ]
            if missing:
                raise serializers.ValidationError({
                    f: "Required for multiplayer games." for f in missing
                })

        return data

    def create(self, validated_data):
        # Pop player_id — we don't use it, we use request.user
        validated_data.pop("player_id", None)
        validated_data["player"] = self.context["request"].user
        return super().create(validated_data)

class GameHistorySerializer(serializers.ModelSerializer):
    """Exact fields from the PDF – nothing more."""
    class Meta:
        model = GameHistory
        fields = [
            "match_id",
            "game_type", "game_mode", "operation",
            "grid_size", "timestamp", "status",
            "final_score", "accuracy_percentage", "hints_used",
            "completion_time", "room_code", "position", "total_players",
            "points_earned",
        ]
        read_only_fields = fields

class LeaderboardSerializer(serializers.Serializer):
    rank = serializers.IntegerField(read_only=True)
    user_id = serializers.CharField(source="user.id")
    username = serializers.CharField(source="user.username")
    email = serializers.CharField(source="user.email")
    avatar = serializers.CharField(source="avatar.url", allow_null=True)
    total_points = serializers.IntegerField()
    games_played = serializers.IntegerField()