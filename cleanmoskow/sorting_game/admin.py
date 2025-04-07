from django.contrib import admin
from .models import SortingGameSession, SortingGameStart

@admin.register(SortingGameSession)
class SortingGameSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "score", "created_at")
    search_fields = ("id", "user__username")

    change_list_template = "admin/api/sortinggamesession/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        total_games = SortingGameSession.objects.count()
        finished_games = SortingGameSession.objects.all().count()

        start_counter_obj = SortingGameStart.objects.first()
        started_count = start_counter_obj.counter if start_counter_obj else 0
        user_count = SortingGameSession.objects.values("user").distinct().count()

        if started_count > 0:
            completion_rate = round((finished_games / started_count) * 100, 2)
        else:
            completion_rate = 0

        extra_context.update({
            'total_games': total_games,
            'started_users': started_count,
            'user_count': user_count,
            'completion_rate': completion_rate,
        })

        return super().changelist_view(request, extra_context=extra_context)


# @admin.register(SortingGameStart)
# class SortingGameStartAdmin(admin.ModelAdmin):
#     list_display = ("id", "counter")