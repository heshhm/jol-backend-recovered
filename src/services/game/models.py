from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Index

class GameHistory(models.Model):
    """One row = one finished game. Stores ONLY what the API spec demands."""

    class GameType(models.TextChoices):
        SOLO = "solo", "Solo"
        MULTIPLAYER = "multiplayer", "Multiplayer"

    class GameMode(models.TextChoices):
        TIMED = "timed", "Timed"
        UNTIMED = "untimed", "Untimed"

    class Operation(models.TextChoices):
        ADDITION = "addition", "Addition"
        SUBTRACTION = "subtraction", "Subtraction"

    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"
        TIMED_OUT = "timed_out", "Timed Out"

    # Primary key from frontend
    match_id = models.CharField(max_length=36, unique=True, db_index=True)

    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_history",
        db_index=True
    )

    # Core required fields
    game_type = models.CharField(max_length=20, choices=GameType.choices)
    game_mode = models.CharField(max_length=20, choices=GameMode.choices)
    operation = models.CharField(max_length=20, choices=Operation.choices)
    grid_size = models.PositiveSmallIntegerField()
    timestamp = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices)

    # Performance summary
    final_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Client-reported score – also used as points_earned"
    )
    accuracy_percentage = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="correct_cells / total_player_cells * 100"
    )
    hints_used = models.PositiveSmallIntegerField(default=0)

    # GAME POINTS
    points_earned = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Equals final_score for completed games, 0 otherwise"
    )

    # Conditional / multiplayer-only
    completion_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Seconds to complete – required only for timed mode"
    )
    room_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        db_index=True,
        help_text="6-char room code – NULL for solo"
    )
    position = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Player rank – NULL for solo"
    )
    total_players = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Number of players in room – NULL for solo"
    )

    class Meta:
        verbose_name_plural = "Game History"
        indexes = [
            Index(fields=["player", "-timestamp"]),          # Personal history
            Index(fields=["-timestamp"]),                    # Global leaderboards
            Index(fields=["room_code", "-timestamp"]),       # Room results
        ]
        constraints = [
            models.UniqueConstraint(fields=["match_id"], name="unique_match_id")
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.player} – {self.match_id} – {self.final_score}pts"

    def save(self, *args, **kwargs):
        # Non-completed games earn 0 points; otherwise passthrough final_score
        if self.status == self.Status.COMPLETED:
            self.points_earned = self.final_score
        else:
            self.points_earned = 0
        super().save(*args, **kwargs)