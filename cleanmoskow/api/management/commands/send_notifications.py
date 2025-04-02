from django.core.management.base import BaseCommand
from accounts.models import TelegramUser
from api.models import Notification
from django.utils import timezone

class Command(BaseCommand):
    help = 'Отправить уведомления нескольким пользователям'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=str, help='Список пользователей через запятую (например: 1,2,3)')
        parser.add_argument('--message', type=str, help='Текст уведомления')
        parser.add_argument('--send_at', type=str, help='Дата и время отправки в формате YYYY-MM-DD HH:MM')

    def handle(self, *args, **kwargs):
        # Получаем список пользователей
        user_ids = kwargs['users'].split(',')
        users = TelegramUser.objects.filter(id__in=user_ids)
        
        # Получаем сообщение и время отправки
        message = kwargs['message']
        send_at = timezone.datetime.strptime(kwargs['send_at'], "%Y-%m-%d %H:%M")

        # Создаем уведомление и добавляем пользователей
        notification = Notification.objects.create(
            title="Уведомление",
            message=message,
            send_at=send_at
        )

        notification.users.set(users)  # Добавляем пользователей к уведомлению

        self.stdout.write(f"Уведомление для {users.count()} пользователей создано для отправки на {send_at}")
        self.stdout.write("Уведомление успешно создано.")
