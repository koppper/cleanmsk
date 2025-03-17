from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from oauth2_provider.models import AccessToken
from django.utils.timezone import now
from rest_framework import status
import logging
from rest_framework.response import Response

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
class TokenAuthMiddleware(MiddlewareMixin):
    """Middleware для авторизации через access_token из cookies"""

    def process_request(self, request):
        exempt_paths = [
            "/admin/",
            "/swagger",
            "/accounts/auth/"
        ]

        # Если путь начинается с "/admin/", не выполняем проверку токена
        if any(request.path.startswith(path) for path in exempt_paths):
            return None  

        token = request.COOKIES.get("access_token")
        logger.info(f"token: {token}")

        if not token:
            logger.info(f"if not token:: {token}")

            # request.user = None 
            # return None
            return JsonResponse({"error": "Требуется авторизация"}, status=401)

        try:
            access_token = AccessToken.objects.get(token=token)
            if access_token.expires < now():
                return JsonResponse({"error": "Токен истёк"}, status=401)

            request.user = access_token.user
            if "Authorization" not in request.headers:
                request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        except AccessToken.DoesNotExist:
            return JsonResponse({"error": "Неверный токен"}, status=401)
