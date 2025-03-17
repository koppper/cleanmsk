from django.contrib import admin
from .models import User, TelegramUser


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'telegram_id', 'created_at', 'location_requests_count')
    search_fields = ('telegram_id', 'username')
    
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        total_users = User.objects.count()
        total_telegram_users = TelegramUser.objects.filter(user__isnull=False).count()

        extra_context['total_users'] = total_users
        extra_context['total_telegram_users'] = total_telegram_users

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