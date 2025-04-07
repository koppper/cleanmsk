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
            "/api/accounts/login/",
            "/api/accounts/register/",

            "/api/admin/",
            "/api/swagger",
            "/api/accounts/auth/"
        ]

        if any(request.path.startswith(path) for path in exempt_paths):
            return None  
        token = request.COOKIES.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]  # Берём сам токен без "Bearer"
                logger.info(f"🔑 Токен найден в Authorization-заголовке: {token}")

        if not token:
            logger.warning("Токен отсутствует в куках и заголовке Authorization")
            return JsonResponse({"error": "Требуется авторизация"}, status=401)

        try:
            access_token = AccessToken.objects.get(token=token)
            if access_token.expires < now():
                logger.warning("Токен истёк")
                return JsonResponse({"error": "Токен истёк"}, status=401)

            request.user = access_token.user
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"

            logger.info(f"✅ Пользователь авторизован: {request.user}")

        except AccessToken.DoesNotExist:
            logger.warning("❌ Неверный токен")
            return JsonResponse({"error": "Неверный токен"}, status=401)
