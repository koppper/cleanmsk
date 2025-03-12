from django.contrib import admin
from .models import SortingGameSession

@admin.register(SortingGameSession)
class SortingGameSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "score", "created_at")
    search_fields = ("id",)

    change_list_template = "admin/api/sortinggamesession/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        extra_context['total_games'] = SortingGameSession.objects.count()

        return super().changelist_view(request, extra_context=extra_context)
