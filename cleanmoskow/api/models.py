from django.db import models
from django.utils import timezone
from accounts.models import TelegramUser
from ckeditor.fields import RichTextField



class MessageTemplate(models.Model):
    class TemplateType(models.TextChoices):
        MESSAGE = "message", "Сообщение"
        BUTTON = "button", "Кнопка"
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    text = models.TextField(verbose_name="Текст")
    type = models.CharField(
        max_length=20,
        choices=TemplateType.choices,
        default=TemplateType.MESSAGE,
        verbose_name="Тип шаблона"
    )
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Шаблон"
        verbose_name_plural = "Шаблоны"


class Category(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория пункта"
        verbose_name_plural = "Категории пунктов"


class Points(models.Model):
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    address = models.TextField(verbose_name="Адрес")
    link = models.URLField(null=True, blank=True, verbose_name="Ссылка")
    title = models.CharField(max_length=255, verbose_name="Название точки")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    restricted = models.BooleanField(default=False, verbose_name="Ограниченный доступ")
    categories = models.CharField(max_length=100, blank=True, null=True)
    businesHoursState = models.JSONField(verbose_name="Часы работы", blank=True, null=True,)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

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


class AdviceCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название категории")
    image = models.ImageField(upload_to="advices/", blank=True, null=True, verbose_name="Фото", help_text="Изображение не должно превышать 80x91px.")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Вопрос FAQ"
        verbose_name_plural = "Вопросы FAQ"


class Advice(models.Model):
    # text = models.CharField(max_length=255, verbose_name="Заголовок совета")
    description = RichTextField(verbose_name="Ответ на вопрос")
    category = models.ForeignKey(AdviceCategory, on_delete=models.CASCADE, blank=True, null=True, related_name="advices", verbose_name="Категория" )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    order = models.PositiveIntegerField(default=1, verbose_name="Очерёдность")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return str(self.order)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["order", "created_at"]


class Notification(models.Model):
    users = models.ManyToManyField(TelegramUser, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    sent = models.BooleanField(default=False)
    send_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification: {self.title} for {self.users.count()} users"

    class Meta:
        ordering = ['send_at']
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
