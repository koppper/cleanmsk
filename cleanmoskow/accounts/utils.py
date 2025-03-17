import hashlib
import hmac
import urllib.parse
from django.conf import settings

def verify_telegram_data(init_data: str) -> bool:
    """Проверяет подпись Telegram"""
    token = settings.TELEGRAM_BOT_TOKEN
    secret_key = hashlib.sha256(token.encode()).digest()

    parsed_data = dict(urllib.parse.parse_qsl(init_data))
    hash_value = parsed_data.pop("hash", None)

    check_string = "\n".join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
    expected_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    return expected_hash == hash_value
