from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
import uuid
from django.db import models


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

    # USERNAME_FIELD = 'username'
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username or f"User ({self.telegram_id})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class MessageTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    text = models.TextField(verbose_name="Текст")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Шаблон сообщения"
        verbose_name_plural = "Шаблоны сообщений"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_ru = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория отходов"
        verbose_name_plural = "Категории отходов"
        

class Points(models.Model):
    latitude = models.FloatField(verbose_name="Широта")  # Извлекаем из geom
    longitude = models.FloatField(verbose_name="Долгота")  # Извлекаем из geom
    address = models.TextField(verbose_name="Адрес")  # Сохраняем адрес
    title = models.CharField(max_length=255, verbose_name="Название точки")  # Название пункта
    description = models.TextField(blank=True, null=True, verbose_name="Описание")  # Описание (если есть)
    restricted = models.BooleanField(default=False, verbose_name="Ограниченный доступ")  # Флаг ограниченного доступа
    categories = models.CharField(max_length=100, blank=True, null=True)
    businesHoursState = models.JSONField(verbose_name="Часы работы", blank=True, null=True,)  # Форматируем часы работы

    def __str__(self):
        return f"{self.title} ({self.address})"
    
    def format_business_hours(self):
        """Форматирование часов работы в читаемый вид"""
        days = ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        formatted_hours = []
        for index, day in enumerate(days):
            if self.businesHoursState.get(day):
                formatted_hours.append(f"{day}: {self.businesHoursState[day]}")
            else:
                formatted_hours.append(f"{day}: выходной")
        return "\n".join(formatted_hours)

    class Meta:
        verbose_name = "Пункт выдачи"
        verbose_name_plural = "Пункты выдачи"


class TelegramUser(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="telegram_profile"
    )
    telegram_id = models.CharField(max_length=50, unique=True)  # Telegram ID
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.telegram_id})"


class Advice(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок совета")
    description = models.TextField(verbose_name="Ответ на вопрос")
    image = models.ImageField(upload_to="advices/", blank=True, null=True, verbose_name="Фото")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title
