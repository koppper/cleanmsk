from celery import shared_task
from django.utils import timezone
from api.models import Notification
import telegram
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_telegram_notification(notification_id):
    """Отправка уведомления через telegram bot."""
    logger.info(f"start celery task")
    try:
        notification = Notification.objects.get(id=notification_id)
        bot = telegram.Bot(token="7546363316:AAEtCZQrvrAbsOFlRm6bd30r4Xjatlcw4_I")

        for user in notification.users.all():
            bot.send_message(chat_id=user.telegram_id, text=notification.message)
            logger.info(f"Уведомление отправлено пользователю {user.username}")

        notification.sent = True
        notification.save()

        logger.info(f"Уведомление для {notification.users.count()} пользователей отправлено.")

    except Notification.DoesNotExist:
        logger.error(f"Уведомление с ID {notification_id} не найдено.")
