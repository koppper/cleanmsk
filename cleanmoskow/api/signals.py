# api/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from api.models import Notification
import logging
import json

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification, weak=False)
def schedule_notification_task(sender, instance, created, **kwargs):
    """Планирование задачи для уведомления."""
    logger.info("schedule_notification_task triggered")
    if instance.sent:
        return
    task_name = f"Notification-{instance.id}"
    logger.info(f"Scheduling task for {task_name}")

    PeriodicTask.objects.filter(name=task_name).delete()
    if created:
        logger.info("Created new Notification -> scheduling")
    elif instance.send_at != instance.created_at:
        logger.info("Changed send_at -> scheduling")
    else:
        logger.info("No changes to send_at -> not scheduling")

    if created or instance.send_at != instance.created_at:
        logger.info("Creating ClockedSchedule")
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=instance.send_at
        )

        PeriodicTask.objects.create(
            clocked=clocked,
            one_off=True,
            name=task_name,
            task="api.tasks.send_telegram_notification",
            args=json.dumps([str(instance.id)]),
        )

        logger.info(f"Создана новая задача {task_name} на {instance.send_at}")
    else:
        logger.info(f"Уведомление {task_name} не требует изменения времени.")
