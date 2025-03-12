from django.db import models
from api.models import TelegramUser

class SortingGameSession(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="game_sessions")
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Игра {self.id} - {self.user.first_name} - Очки: {self.score}"

