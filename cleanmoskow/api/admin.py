from django.contrib import admin
from .models import MessageTemplate, Points, Category, Advice, AdviceCategory, Notification
import json
from django.shortcuts import render
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import admin, messages
from django.utils.html import format_html
from rangefilter.filters import DateTimeRangeFilter
from ckeditor.widgets import CKEditorWidget
from django.db import models
from django import forms
from PIL import Image
from django.core.exceptions import ValidationError

from django_celery_beat.models import (
    IntervalSchedule,
    CrontabSchedule,
    ClockedSchedule,
    SolarSchedule,
)

from oauth2_provider.models import (
    AccessToken,
    RefreshToken,
    Application,
    Grant,
    IDToken,
)

MODELS_TO_UNREGISTER = [
    IntervalSchedule,
    CrontabSchedule,
    ClockedSchedule,
    SolarSchedule,
    AccessToken,
    RefreshToken,
    Application,
    Grant,
    IDToken,
]

for model in MODELS_TO_UNREGISTER:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

def safe_decode(text):
    try:
        if isinstance(text, str):
            # Если содержит \u — возможно, это Unicode-escape
            if "\\u" in text:
                return text.encode().decode("unicode_escape")
        return text
    except Exception:
        return text


@admin.register(Points)
class PointsAdmin(admin.ModelAdmin):
    list_display = ("title", "address", "categories")
    actions = ["import_json"]
    change_list_template = 'admin/api/points/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name="points_import_json")
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:points_import_json')
        return super().changelist_view(request, extra_context=extra_context)

    def import_json_view(self, request):
        if request.method == "POST" and request.FILES.get("json_file"):
            json_file = request.FILES["json_file"]
            try:
                data = json.load(json_file)
                data_block = data.get("data")
                if not data_block or not isinstance(data_block, dict):
                    self.message_user(request, "❌ Ошибка: неверный формат JSON (нет data или это не словарь)", messages.ERROR)
                    return HttpResponseRedirect("../")

                points = data_block.get("points", [])
                if not isinstance(points, list):
                    self.message_user(request, "❌ Ошибка: 'points' не является списком", messages.ERROR)
                    return HttpResponseRedirect("../")

                added = 0
                duplicates = 0

                for point in points:
                    if not point.get("geom") or not point.get("address") or not point.get("title") or not point.get("categories"):
                        continue

                    coords = point["geom"].replace("POINT(", "").replace(")", "").split()
                    longitude, latitude = float(coords[0]), float(coords[1])
                    address = point["address"]
                    title = point["title"]
                    category_name = point["categories"][0] if point["categories"] else None

                    if not category_name:
                        continue

                    category, _ = Category.objects.get_or_create(name=category_name)

                    exists = Points.objects.filter(
                        latitude=latitude,
                        longitude=longitude,
                        address=address,
                        title=title,
                        categories=category
                    ).exists()

                    if exists:
                        duplicates += 1
                        continue

                    schedule = point.get("businesHoursState", {}).get("schedule")
                    business_hours = {
                        "пн": "",
                        "вт": "",
                        "ср": "",
                        "чт": "",
                        "пт": "",
                        "сб": "",
                        "вс": "",
                    }
                    if schedule:
                        weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"]
                        for entry in schedule:
                            dow = entry["dow"]
                            open_time = entry["opens"][0] if entry["opens"] else "00:00"
                            close_time = entry["closes"][0] if entry["closes"] else "00:00"
                            business_hours[weekdays[dow]] = f"{open_time} - {close_time}"

                    Points.objects.create(
                        latitude=latitude,
                        longitude=longitude,
                        address=address,
                        title=title,
                        description=point.get("pointDescription", ""),
                        restricted=point.get("restricted", False),
                        categories=category,
                        businesHoursState=business_hours,
                        link=point.get("link", "")
                    )
                    added += 1

                self.message_user(
                    request,
                    f"✅ Импорт завершён: {added} добавлено, {duplicates} дубликатов пропущено.",
                    messages.SUCCESS
                )
                return HttpResponseRedirect("../")

            except Exception as e:
                self.message_user(request, f"❌ Ошибка: {e}", messages.ERROR)
                return HttpResponseRedirect("../")

        return render(request, "admin/api/points/import_json.html")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_ru")
    search_fields = ("name", "name_ru")


class AdviceAdminForm(forms.ModelForm):
    class Meta:
        model = Advice
        fields = '__all__'
        widgets = {
            'description': CKEditorWidget(),
        }


class AdviceInline(admin.StackedInline): 
    model = Advice
    form = AdviceAdminForm
    extra = 0
    verbose_name = "Ответ"


class AdviceCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = AdviceCategory
        fields = '__all__'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            img = Image.open(image)
            max_width, max_height = 80, 91
            if img.width > max_width or img.height > max_height:
                raise ValidationError(f"Изображение не должно превышать {max_width}x{max_height}px. "
                                      f"Текущее: {img.width}x{img.height}px.")
        return image


@admin.register(AdviceCategory)
class AdviceCategoryAdmin(admin.ModelAdmin):
    form = AdviceCategoryAdminForm
    inlines = [AdviceInline]

    list_display = ('id', 'name')
    search_fields = ('name',)


# @admin.register(Advice)
# class AdviceAdmin(admin.ModelAdmin):
#     form = AdviceAdminForm
#     list_display = ("title", "category", "created_at")
#     list_filter = ("category",)
#     search_fields = ("title", "description")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ( 'title', 'message', 'send_at', 'sent')
    list_filter = (('send_at', DateTimeRangeFilter), 'sent')
    search_fields = ('title', 'message')

    def has_change_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            cl = response.context_data['cl']
            filtered_qs = cl.queryset
            sent_count = filtered_qs.filter(sent=True).count()

            response.context_data.update({
                'sent_count': sent_count,
            })
        except (AttributeError, KeyError):
            pass

        return response


@admin.register(MessageTemplate)
class MessageTemplateyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'text', 'type')
    search_fields = ('name', 'text', 'type')
