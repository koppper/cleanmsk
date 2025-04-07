from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import TelegramUser, User
from .serializers import TelegramUserSerializer, LoginSerializer, RegisterSerializer
from .utils import verify_telegram_data
import uuid
from games.serializers import TelegramIdSerializer
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.settings import oauth2_settings
from django.utils.timezone import now
from datetime import timedelta
from games.models import Leaderboard
from .utils import censor


# class AuthAPIView(APIView):
#     """Регистрация или логин пользователя по Telegram ID"""
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(
#         request_body=LoginSerializer,
#         responses={200: openapi.Response("Успешный ответ", TelegramUserSerializer)},
#     )
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         telegram_id = serializer.validated_data["telegram_id"]
#         username = serializer.validated_data.get("username")
#         telegram_user = TelegramUser.objects.filter(telegram_id=telegram_id).first()

#         if not telegram_user:
#             user = User.objects.create(
#                 telegram_id=telegram_id,
#                 username=username or f"user_{telegram_id}"
#             )
#             telegram_user = TelegramUser.objects.create(
#                 user=user,
#                 uuid=uuid.uuid4(),
#                 username=username,
#                 telegram_id=telegram_id
#             )

#         token = AccessToken.objects.create(
#             user=telegram_user.user,
#             token=str(uuid.uuid4()),
#             expires=now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
#             scope="read write"
#         )

#         response = Response({
#             "message": "Успешный вход",
#             "access_token": token.token,
#             "expires": token.expires,
#         }, status=status.HTTP_200_OK)

#         response.set_cookie(
#             key="access_token",
#             value=token.token,
#             httponly=True,
#             secure=True,
#             samesite="Lax",
#             max_age=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
#         )
#         response["Authorization"] = f"Bearer {token.token}"

#         return response


class LoginAPIView(APIView):
    """Логин по Telegram ID (без регистрации)"""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response("Успешный ответ", TelegramUserSerializer)},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        telegram_id = serializer.validated_data["telegram_id"]

        telegram_user = TelegramUser.objects.filter(telegram_id=telegram_id).first()

        if not telegram_user:
            return Response({"error": "Пользователь не зарегистрирован"}, status=status.HTTP_404_NOT_FOUND)

        token = AccessToken.objects.create(
            user=telegram_user.user,
            token=str(uuid.uuid4()),
            expires=now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
            scope="read write"
        )

        response = Response({
            "message": "Успешный вход",
            "access_token": token.token,
            "expires": token.expires,
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key="access_token",
            value=token.token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )
        response["Authorization"] = f"Bearer {token.token}"

        return response


class RegisterAPIView(APIView):
    """Регистрация нового пользователя по Telegram ID"""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: openapi.Response("Зарегистрирован", TelegramUserSerializer)},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        telegram_id = serializer.validated_data["telegram_id"]
        username = serializer.validated_data.get("username")
        censored_username = censor(username) if username else f"user_{telegram_id}"

        if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
            return Response({"detail": "Пользователь уже зарегистрирован"}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={"username": username or f"user_{telegram_id}"}
        )

        telegram_user = TelegramUser.objects.create(
            user=user,
            uuid=uuid.uuid4(),
            username=censored_username,
            telegram_id=telegram_id
        )

        token = AccessToken.objects.create(
            user=user,
            token=str(uuid.uuid4()),
            expires=now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
            scope="read write"
        )

        response = Response({
            "message": "Успешная регистрация",
            "access_token": token.token,
        }, status=status.HTTP_201_CREATED)

        response.set_cookie(
            key="access_token",
            value=token.token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )
        response["Authorization"] = f"Bearer {token.token}"

        return response


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
