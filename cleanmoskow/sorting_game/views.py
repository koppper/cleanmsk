from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import SortingGameSession, SortingGameStart
from games.models import Leaderboard
from .serializers import SortingGameSessionSerializer, SortingGameSessionHistorySerializer
from games.serializers import LeaderboardSerializer, TelegramIdSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.utils import log_user_action

from accounts.models import TelegramUser 

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class StartSortingGameSession(APIView):
    """Создание новой игры"""
    # authentication_classes = []
    @swagger_auto_schema(
        operation_description="Запуск новой игры",
        request_body=SortingGameSessionSerializer,
        responses={201: openapi.Response("Игра началась", SortingGameSessionSerializer)}
    )
    def post(self, request):
        serializer = SortingGameSessionSerializer(data=request.data)
        telegram_user = request.user.telegram_profile
        log_user_action(request, "game_start")

        if serializer.is_valid():
            game_session = serializer.save(user=telegram_user)
            # user = game_session.user
            score = game_session.score

            leaderboard_entry, created = Leaderboard.objects.get_or_create(
                user=telegram_user,
                defaults={"score": 0}
            )

            leaderboard_entry.score += score
            leaderboard_entry.save()

            return Response(
                {
                    "message": "Игра началась",
                    "game_id": game_session.id,
                    "total_score": leaderboard_entry.score,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SortingGameHistory(APIView):
    """Получить историю завершённых игр пользователя по `uuid`"""

    def get(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)

        telegram_user = request.user.telegram_profile

        games = SortingGameSession.objects.filter(user=telegram_user).order_by("-created_at")

        if not games.exists():
            return Response({"message": "Нет игр"}, status=status.HTTP_404_NOT_FOUND)
        leaderboard_entry = Leaderboard.objects.filter(user=telegram_user).first()
        total_score = leaderboard_entry.score if leaderboard_entry else 0
        user_rank = (
            Leaderboard.objects
            .filter(score__gt=total_score)
            .count() + 1
        ) if leaderboard_entry else None
        return Response({
            "total_score": total_score,
            "user_rank": user_rank,
            "games": SortingGameSessionSerializer(games, many=True).data
        }, status=status.HTTP_200_OK)
    


@method_decorator(csrf_exempt, name='dispatch')
class StartSortingGame(APIView):
    """Увеличивает счётчик запусков сортировочной игры"""

    def post(self, request):
        obj, _ = SortingGameStart.objects.get_or_create(id=1)
        obj.counter += 1
        obj.save()
        return Response({"counter": obj.counter}, status=status.HTTP_200_OK)