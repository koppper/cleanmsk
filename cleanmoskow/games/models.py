from django.db import models
from api.models import TelegramUser


class QuizQuestions(models.Model):
    question = models.TextField(verbose_name="Вопрос")
    answers = models.JSONField(verbose_name="Ответы")
    correct_answer = models.IntegerField(verbose_name="Правильный ответ")
    explanation = models.TextField(null=True, blank=True)
    tip_link = models.URLField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="images/")

    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class Leaderboard(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=255)
    score = models.FloatField()
    
    def __str__(self):
        return f"Лидерборд пользователя {self.user}"
    
    class Meta:
        verbose_name = "Лидерборд"
        verbose_name_plural = "Лидерборды"
        ordering = ["-score"]


class GameSession(models.Model):

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    questions = models.JSONField()
    answered_questions = models.JSONField(default=list)
    current_question_index = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=5)
    finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Игровая сессия пользователя {self.user}"
    
    
    class Meta:
        verbose_name = "Игровая сессия"
        verbose_name_plural = "Игровые сессии"