from django.db import models
from accounts.models import TelegramUser
import re

# CENSORED_WORDS = ["плохое_слово1", "плохое_слово2"]

class QuizQuestions(models.Model):
    question = models.TextField(verbose_name="Вопрос")
    answers = models.JSONField(verbose_name="Ответы")
    correct_answer = models.IntegerField(verbose_name="Правильный ответ")
    explanation = models.TextField(null=True, blank=True)
    tip_link = models.URLField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="images/")
    total_answers = models.IntegerField(default=0, verbose_name="Всего ответов")
    correct_answers = models.IntegerField(default=0, verbose_name="Правильных ответов")

    def correct_percentage(self):
        if self.total_answers == 0:
            return "0%"
        return f"{round((self.correct_answers / self.total_answers) * 100)}%"

    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class CensoredWord(models.Model):
    word = models.CharField(max_length=255, unique=True, verbose_name="Запрещённое слово")

    def __str__(self):
        return self.word

    class Meta:
        verbose_name = "Цензурное слово"
        verbose_name_plural = "Цензурные слова"


class Leaderboard(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    # username = models.CharField(max_length=255)
    score = models.FloatField()

    # def censor_username(self):
    #     """Фильтруем username, заменяя запрещенные слова на звёздочки"""
    #     username = self.user.username if self.user and self.user.username else "Null"
    #     censored_words = CensoredWord.objects.values_list("word", flat=True)

    #     for word in censored_words:
    #         pattern = re.compile(re.escape(word), re.IGNORECASE)
    #         username = pattern.sub("*" * len(word), username)

    #     return username

    def __str__(self):
        return self.user.username if self.user and self.user.username else "Unknown"

    
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
        verbose_name = "Игровая сессия квиза"
        verbose_name_plural = "Игровые сессии квизов"
        ordering = ['-created_at']