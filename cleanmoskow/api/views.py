from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Advice
from .serializers import AdviceSerializer
import uuid
from rest_framework.generics import ListAPIView
from games.serializers import TelegramIdSerializer
from accounts.models import TelegramUser


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