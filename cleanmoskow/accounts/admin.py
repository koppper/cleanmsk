from django.contrib import admin
from .models import User, TelegramUser, UserActivity
from django.utils.timezone import now, timedelta
from django.db.models import Count
from django.db.models import Sum


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'telegram_id', 'created_at', 'location_requests_count')
    search_fields = ('telegram_id', 'username')
    
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        total_users = User.objects.count()
        total_telegram_users = TelegramUser.objects.filter(user__isnull=False).count()

        total_location_requests = User.objects.aggregate(total=Sum('location_requests_count'))['total'] or 0

        extra_context.update({
            'total_users': total_users,
            'total_telegram_users': total_telegram_users,
            'total_location_requests': total_location_requests,
        })

        return super().changelist_view(request, extra_context=extra_context)


class TelegramUserAdmin(admin.ModelAdmin):
    model = TelegramUser
    list_display = ('user', 'telegram_id', 'uuid', "first_name", "last_name", "created_at")
    list_filter = ('created_at', ('user', admin.BooleanFieldListFilter))
    search_fields = ('telegram_id', 'uuid', "first_name", "last_name")
    ordering = ('-created_at',)

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        total_telegram_users = TelegramUser.objects.count()
        users_with_profiles = TelegramUser.objects.filter(user__isnull=False).count()

        extra_context['total_telegram_users'] = total_telegram_users
        extra_context['users_with_profiles'] = users_with_profiles

        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(TelegramUser, TelegramUserAdmin)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp")
    list_filter = ("action", "timestamp")
    ordering = ("-timestamp",)
    change_list_template = "admin/user_activity_changelist.html"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        today = now()
        extra_context["DAU"] = UserActivity.objects.filter(timestamp__gte=today - timedelta(days=1)).values("user").distinct().count()
        extra_context["WAU"] = UserActivity.objects.filter(timestamp__gte=today - timedelta(days=7)).values("user").distinct().count()
        extra_context["MAU"] = UserActivity.objects.filter(timestamp__gte=today - timedelta(days=30)).values("user").distinct().count()

        feature_usage = (
            UserActivity.objects
            .values("action")
            .annotate(count=Count("id"))
        )

        action_display_map = dict(UserActivity.ACTIONS)
        feature_usage = [
            {"action": action_display_map.get(item["action"], item["action"]), "count": item["count"]}
            for item in feature_usage
        ]

        total_actions = sum(item["count"] for item in feature_usage)

        extra_context.update({
            "feature_usage": feature_usage,
            "total_actions": total_actions,
        })

        return super().changelist_view(request, extra_context=extra_context)
