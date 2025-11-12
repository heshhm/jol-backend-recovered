# game/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Index, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction


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
    final_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
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
        help_text="Points calculated from accuracy, hints, time, position"
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

    # ──────────────────────────────────────────────────────────────
    # SCORING ENGINE – used by both signal & leaderboard queries
    # ──────────────────────────────────────────────────────────────
    @property
    def calculated_points(self) -> int:
        """
        Dynamic points calculation – used for:
        • Real-time leaderboard (today/week/month)
        • Total points accumulation in UserProfile
        """
        if self.status != self.Status.COMPLETED:
            return 0

        points = 100  # base

        # 1. ACCURACY BONUS (max +40)
        acc = self.accuracy_percentage or 0
        if acc >= 95:
            points += 40
        elif acc >= 85:
            points += 35
        elif acc >= 75:
            points += 30
        elif acc >= 65:
            points += 25
        elif acc >= 50:
            points += 20
        elif acc >= 25:
            points += 10

        # 2. HINTS PENALTY (max -20)
        hints = self.hints_used or 0
        if hints >= 5:
            points -= 20
        elif hints >= 3:
            points -= 15
        elif hints == 2:
            points -= 10
        elif hints == 1:
            points -= 5

        # 3. TIME BONUS (timed mode only, max +30)
        if self.game_mode == self.GameMode.TIMED and self.completion_time:
            gold = self.grid_size * 30    # 4×4 → 120s, 5×5 → 150s, etc.
            silver = self.grid_size * 45
            bronze = self.grid_size * 60

            t = self.completion_time
            if t <= gold:
                points += 30
            elif t <= silver:
                points += 15
            elif t <= bronze:
                points += 5

        # 4. MULTIPLAYER POSITION BONUS (max +30)
        if self.game_type == self.GameType.MULTIPLAYER and self.position:
            if self.position == 1:
                points += 30
            elif self.position == 2:
                points += 20
            elif self.position == 3:
                points += 10

        return max(10, points)  # never below 10
