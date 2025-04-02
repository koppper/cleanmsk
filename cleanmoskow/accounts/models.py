from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
import uuid
from django.db import models
from django.utils.timezone import now
from django.contrib.postgres.fields import ArrayField


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("username обязателен")
        username = self.normalize_email(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, max_length=150, blank=False, null=False, verbose_name="Имя пользователя")
    telegram_id = models.BigIntegerField(verbose_name="Telegram ID", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    location_requests_count = models.IntegerField(default=0)

    groups = models.ManyToManyField(Group, blank=True)
    user_permissions = models.ManyToManyField(Permission, blank=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username or f"User ({self.telegram_id})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class TelegramUser(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="telegram_profile"
    )
    telegram_id = models.CharField(max_length=50, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    onboarding_seen = models.BooleanField(default=False)
    onboarding_second_seen = models.BooleanField(default=False)
    answered_questions_ids = ArrayField(
        base_field=models.IntegerField(),
        default=list,
        blank=True, null=True,
        verbose_name="ID вопросов, на которые пользователь уже ответил"
    )
    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = "Телеграм пользователь"
        verbose_name_plural = "Телеграм пользователи"


class UserActivity(models.Model):
    ACTIONS = [
        ('quiz_start', 'Запуск квиза'),
        ('game_start', 'Запуск игры'),
        ('location_request', 'Запрос геолокации'),
        ('faq_open', 'Открытие FAQ'),
    ]
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    action = models.CharField(max_length=100, choices=ACTIONS)
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp}"

    class Meta:
        verbose_name = "Активность пользователя"
        verbose_name_plural = "Активности пользователей"