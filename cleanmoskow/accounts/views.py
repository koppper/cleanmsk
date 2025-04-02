from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import TelegramUser, User
from .serializers import TelegramUserSerializer, LoginSerializer
from .utils import verify_telegram_data
import uuid
from games.serializers import TelegramIdSerializer
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.settings import oauth2_settings
from django.utils.timezone import now
from datetime import timedelta


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid
from datetime import timedelta
from oauth2_provider.models import AccessToken
from oauth2_provider.settings import oauth2_settings

from .models import User, TelegramUser
from .serializers import TelegramUserSerializer, LoginSerializer


class AuthAPIView(APIView):
    """Регистрация или логин пользователя по Telegram ID"""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response("Успешный ответ", TelegramUserSerializer)},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        telegram_id_value = serializer.validated_data["telegram_id"]

        telegram_user = TelegramUser.objects.filter(telegram_id=telegram_id_value).first()

        if not telegram_user:
            user = get_object_or_404(User, telegram_id=telegram_id_value)

            telegram_user = TelegramUser.objects.create(
                user=user,
                uuid=uuid.uuid4(),
                username=user.username,
                telegram_id=user.telegram_id
            )

        token = AccessToken.objects.create(
            user=telegram_user.user,
            token=str(uuid.uuid4()),
            expires=now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
            scope="read write"
        )

        response = Response({
            "message": "Успешный вход",
            "access_token": token.token,
            "expires": token.expires
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key="access_token",
            value=token.token,
            httponly=True,  # Защита от XSS
            secure=True,  # Отправлять только по HTTPS
            samesite="Lax",  # Защита от CSRF
            max_age=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )
        response["Authorization"] = f"Bearer {token.token}"

        return response



# class RegisterUserAPIView(APIView):
#     """Регистрация пользователя по Telegram ID"""

#     @swagger_auto_schema(
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=["telegram_id", "initData"],
#             properties={
#                 "telegram_id": openapi.Schema(type=openapi.TYPE_STRING, description="Уникальный Telegram ID пользователя"),
#                 "initData": openapi.Schema(type=openapi.TYPE_STRING, description="Данные инициализации Telegram WebApp"),
#                 "username": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя", nullable=True),
#                 "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя", nullable=True),
#                 "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия", nullable=True),
#             },
#         ),
#         responses={
#             200: openapi.Response("Успешный ответ", TelegramUserSerializer),
#             400: openapi.Response("Ошибка в запросе"),
#             403: openapi.Response("Недействительные данные Telegram"),
#         },
#     )
#     def post(self, request):
#         data = request.data
#         telegram_id = data.get("telegram_id")
#         username = data.get("username", "")
#         first_name = data.get("first_name", "")
#         last_name = data.get("last_name", "")

#         if not telegram_id:
#             return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

#         user = User.objects.get(telegram_id=telegram_id)
#         if not user:
#             return Response({"error": "user not found"}, status=status.HTTP_400_BAD_REQUEST)
#         telegram_user, telegram_created = TelegramUser.objects.get_or_create(
#             user=user,
#             defaults={
#                 "uuid": uuid.uuid4(),
#                 "username": username,
#                 "telegram_id": telegram_id,
#                 "first_name": first_name,
#                 "last_name": last_name,
#             },
#         )

#         serializer = TelegramUserSerializer(telegram_user)
#         message = "Пользователь зарегистрирован" if telegram_created else "Пользователь уже существует"

#         return Response({"message": message, "user": serializer.data}, status=status.HTTP_200_OK)


# class LoginAPIView(APIView):
#     """Авторизация через OAuth2, выдача только access token"""
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(
#         operation_description="Логин",
#         request_body=LoginSerializer,
#         responses={200: openapi.Response("Пользователь найден.", LoginSerializer)}
#     )
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         uuid_value = serializer.validated_data["uuid"]
        
#         user = get_object_or_404(TelegramUser, uuid=uuid_value).user
#         if not user:
#             return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

#         token = AccessToken.objects.create(
#             user=user,
#             token=str(uuid.uuid4()),
#             expires=now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
#             scope="read write"
#         )
#         response = Response({"message": "success", "access_token": token.token, "expires": token.expires})

#         response.set_cookie(
#                 key="access_token",
#                 value=token,
#                 httponly=True,  # Защита от XSS
#                 secure=True,  # Отправлять только по HTTPS
#                 samesite="Lax",  # Защита от CSRF
#                 max_age=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
#         )
#         response["Authorization"] = f"Bearer {token.token}"

#         return response

from games.models import Leaderboard

class UserProfileView(APIView):
    """Получение данных текущего пользователя"""
    
    def get(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)

        user = request.user
        leaderboard_entry = Leaderboard.objects.filter(user=user.telegram_profile).first()

        return Response({
            "id": user.id,
            "username": user.username,
            "telegram_id": user.telegram_profile.telegram_id,
            "leaderboard": {
                "score": leaderboard_entry.score if leaderboard_entry else None,
                "place": (
                    Leaderboard.objects.filter(score__gt=leaderboard_entry.score).count() + 1
                    if leaderboard_entry else None
                )
            }
        })


class OnboardingView(APIView):
    """Обрабатывает первый онбординг"""

    @swagger_auto_schema(
        operation_description="Отмечает первый онбординг как просмотренный"
    )
    def get(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)

        telegram_user = request.user.telegram_profile
        if not telegram_user:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        if telegram_user.onboarding_seen:
            return Response({"seen": True}, status=status.HTTP_200_OK)

        telegram_user.onboarding_seen = True
        telegram_user.save()

        return Response({
            "seen": False,
            "message": "Onboarding completed"
        }, status=status.HTTP_200_OK)


class SecondOnboardingView(APIView):
    """Обрабатывает второй онбординг"""

    @swagger_auto_schema(
        operation_description="Отмечает второй онбординг как просмотренный"
    )
    def get(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)

        telegram_user = request.user.telegram_profile
        if not telegram_user:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        if telegram_user.onboarding_second_seen:
            return Response({"seen": True}, status=status.HTTP_200_OK)

        telegram_user.onboarding_second_seen = True
        telegram_user.save()

        return Response({
            "seen": False,
            "message": "Second onboarding completed"
        }, status=status.HTTP_200_OK)