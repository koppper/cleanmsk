from django.db import models


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
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    address = models.TextField(verbose_name="Адрес")
    title = models.CharField(max_length=255, verbose_name="Название точки")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    restricted = models.BooleanField(default=False, verbose_name="Ограниченный доступ")
    categories = models.CharField(max_length=100, blank=True, null=True)
    businesHoursState = models.JSONField(verbose_name="Часы работы", blank=True, null=True,)

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


class Advice(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок совета")
    description = models.TextField(verbose_name="Ответ на вопрос")
    image = models.ImageField(upload_to="advices/", blank=True, null=True, verbose_name="Фото")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title
