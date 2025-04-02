from django.db import models
from accounts.models import TelegramUser

class SortingGameSession(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="game_sessions")
    score = models.FloatField(default=0)
    crown = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Игра {self.id} - {self.user.first_name} - Очки: {self.score}"

    class Meta:
        verbose_name = "Сортировочная игра"
        verbose_name_plural = "Сортировочные игры"


class SortingGameStart(models.Model):
    counter = models.IntegerField(default=0)

    def __str__(self):
        return str(self.counter)

    class Meta:
        # verbose_name = "Все игры"
        verbose_name_plural = "Все игры"