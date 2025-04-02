from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from .models import AdviceCategory
from .serializers import AdviceByCategorySerializer
from accounts.utils import log_user_action

class AdviceListByCategoryAPIView(APIView):
    """Список советов, сгруппированных по категориям с поиском"""

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="q",
                in_=openapi.IN_QUERY,
                description="Поиск по заголовку, описанию или названию категории",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", None)

        log_user_action(request, "faq_open")

        categories = AdviceCategory.objects.all()

        if query:
            categories = categories.filter(
                Q(name__icontains=query) |
                Q(advices__title__icontains=query) |
                Q(advices__description__icontains=query)
            ).distinct()

        serializer = AdviceByCategorySerializer(categories, many=True, context={"request": request})
        return Response(serializer.data)
