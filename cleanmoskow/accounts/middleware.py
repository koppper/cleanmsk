from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from oauth2_provider.models import AccessToken
from django.utils.timezone import now
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TokenAuthMiddleware(MiddlewareMixin):
    """Middleware для авторизации через access_token из cookies или заголовка Authorization"""

    def process_request(self, request):

        exempt_paths = [
            "/api/admin/",
            "/api/swagger",
            "/api/accounts/auth/"
        ]

        # Логируем заголовки запроса

        # Пропускаем проверку для определённых путей
        if any(request.path.startswith(path) for path in exempt_paths):
            return None  

        # 🛠 Сначала пробуем достать токен из куков
        token = request.COOKIES.get("access_token")

        # 🛠 Если токена нет в куках, пробуем достать из заголовка Authorization
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]  # Берём сам токен без "Bearer"
                logger.info(f"🔑 Токен найден в Authorization-заголовке: {token}")

        # ❌ Если токена всё ещё нет — отказ в доступе
        if not token:
            logger.warning("❌ Токен отсутствует в куках и заголовке Authorization")
            return JsonResponse({"error": "Требуется авторизация"}, status=401)

        # 🛠 Проверяем токен в базе
        try:
            access_token = AccessToken.objects.get(token=token)
            if access_token.expires < now():
                logger.warning("❌ Токен истёк")
                return JsonResponse({"error": "Токен истёк"}, status=401)

            request.user = access_token.user  # Авторизуем пользователя
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"  # Добавляем токен в META

            logger.info(f"✅ Пользователь авторизован: {request.user}")

        except AccessToken.DoesNotExist:
            logger.warning("❌ Неверный токен")
            return JsonResponse({"error": "Неверный токен"}, status=401)
