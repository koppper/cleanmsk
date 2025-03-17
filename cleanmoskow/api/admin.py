from django.contrib import admin
from .models import MessageTemplate, Points, Category, Advice
import json
from django.shortcuts import render
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import admin, messages
from django.utils.html import format_html


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'text')
    search_fields = ('name', 'text')


@admin.register(Points)
class PointsAdmin(admin.ModelAdmin):
    list_display = ("title", "address", "categories")
    actions = ["import_json"]
    change_list_template = 'admin/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name="points_import_json"),
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
                data = json.load(json_file)  # Загружаем JSON
                points = data.get("data", {}).get("points", [])

                for point in points:
                    # Извлекаем координаты из поля geom
                    coords = point["geom"].replace("POINT(", "").replace(")", "").split()
                    longitude, latitude = float(coords[0]), float(coords[1])

                    # Переформатируем часы работы
                    schedule = point.get("businesHoursState", {}).get("schedule", [])
                    business_hours = {
                        "Sunday": "",
                        "Monday": "",
                        "Tuesday": "",
                        "Wednesday": "",
                        "Thursday": "",
                        "Friday": "",
                        "Saturday": "",
                    }

                    weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                    for entry in schedule:
                        dow = entry["dow"]
                        open_time = entry["opens"][0] if entry["opens"] else "00:00"
                        close_time = entry["closes"][0] if entry["closes"] else "00:00"
                        business_hours[weekdays[dow]] = f"{open_time} - {close_time}"

                    category_name = point["categories"][0] if point["categories"] else None
                    category = Category.objects.filter(name=category_name).first() if category_name else None

                    Points.objects.create(
                        latitude=latitude,
                        longitude=longitude,
                        address=point["address"],
                        title=point["title"],
                        description=point.get("pointDescription", ""),
                        restricted=point.get("restricted", False),
                        categories=category,
                        businesHoursState=business_hours
                    )

                self.message_user(request, "✅ Данные успешно загружены!", messages.SUCCESS)
                return HttpResponseRedirect("../")
            except Exception as e:
                self.message_user(request, f"❌ Ошибка: {e}", messages.ERROR)

        # Рендерим шаблон для загрузки файла
        return render(request, "admin/import_json.html")

    def import_json_link(self, obj):
        # Возвращаем HTML-ссылку для отображения в list_display
        return format_html('<a href="import-json/">Импорт JSON</a>')
    # import_json_link.short_description = "Импорт данных"  # Название колонки

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_ru")
    search_fields = ("name", "name_ru")
    
    


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    list_display = ('title', "description")
    search_fields = ('title', "description")