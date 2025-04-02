import hashlib
import hmac
import urllib.parse
from django.conf import settings
from .models import UserActivity
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def verify_telegram_data(init_data: str) -> bool:
    """Проверяет подпись Telegram"""
    token = settings.TELEGRAM_BOT_TOKEN
    secret_key = hashlib.sha256(token.encode()).digest()

    parsed_data = dict(urllib.parse.parse_qsl(init_data))
    hash_value = parsed_data.pop("hash", None)

    check_string = "\n".join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
    expected_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    return expected_hash == hash_value


def log_user_action(request, action):
    user = getattr(request, 'user', None)
    if user and hasattr(user, 'id'):
        logger.info(f"start log_user_action for user: {user}")
        from .models import UserActivity
        UserActivity.objects.create(user=user, action=action)


