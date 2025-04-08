import logging
from asgiref.sync import sync_to_async
from api.models import MessageTemplate
from accounts.models import User
logger = logging.getLogger(__name__)


async def get_message_template(name: str) -> str:
    try:
        template = await sync_to_async(MessageTemplate.objects.get)(name=name)
        return template.text
    except MessageTemplate.DoesNotExist:
        logger.warning(f"Шаблон {name} не найден.")
        return f"\u26a0\ufe0f Шаблон '{name}' не найден."


async def register_user(telegram_id: int, username: str):
    user, created = await sync_to_async(User.objects.get_or_create)(
        telegram_id=telegram_id,
        defaults={"username": username}
    )
    return user, created


@sync_to_async
def get_all_templates():
    return list(MessageTemplate.objects.all())
