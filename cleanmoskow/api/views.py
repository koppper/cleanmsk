from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import TelegramUser, User, Advice
from .serializers import TelegramUserSerializer, AdviceSerializer
from .utils import verify_telegram_data
import uuid
from rest_framework.generics import ListAPIView



class RegisterUserAPIView(APIView):
    """Регистрация пользователя по Telegram ID"""

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["telegram_id", "initData"],
            properties={
                "telegram_id": openapi.Schema(type=openapi.TYPE_STRING, description="Уникальный Telegram ID пользователя"),
                "initData": openapi.Schema(type=openapi.TYPE_STRING, description="Данные инициализации Telegram WebApp"),
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя", nullable=True),
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя", nullable=True),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия", nullable=True),
            },
        ),
        responses={
            200: openapi.Response("Успешный ответ", TelegramUserSerializer),
            400: openapi.Response("Ошибка в запросе"),
            403: openapi.Response("Недействительные данные Telegram"),
        },
    )
    def post(self, request):
        data = request.data
        telegram_id = data.get("telegram_id")
        username = data.get("username", "")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(telegram_id=telegram_id)
        if not user:
            return Response({"error": "user not found"}, status=status.HTTP_400_BAD_REQUEST)
        telegram_user, telegram_created = TelegramUser.objects.get_or_create(
            user=user,
            defaults={
                "uuid": uuid.uuid4(),
                "username": username,
                "telegram_id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        serializer = TelegramUserSerializer(telegram_user)
        message = "Пользователь зарегистрирован" if telegram_created else "Пользователь уже существует"

        return Response({"message": message, "user": serializer.data}, status=status.HTTP_200_OK)


class GetUserAPIView(APIView):
    """Получение данных пользователя по UUID."""

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "uuid",
                openapi.IN_PATH,
                description="UUID пользователя",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: openapi.Response("Данные пользователя", TelegramUserSerializer),
            404: openapi.Response("Пользователь не найден"),
        },
    )
    def get(self, request, uuid):
        try:
            user = TelegramUser.objects.get(uuid=uuid)
            serializer = TelegramUserSerializer(user)
            return Response({"user": serializer.data}, status=status.HTTP_200_OK)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)


class AdviceListAPIView(ListAPIView):
    """Вывод списка всех советов с возможностью поиска"""
    serializer_class = AdviceSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="q",
                in_=openapi.IN_QUERY,
                description="Поиск по заголовку или описанию",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Обрабатываем GET-запрос с поиском"""
        query = self.request.query_params.get("q", None)
        queryset = Advice.objects.all()

        if query:
            queryset = queryset.filter(title__icontains=query)

        serializer = AdviceSerializer(queryset, many=True)
        return Response(serializer.data)

