from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import SortingGameSession
from games.models import Leaderboard
from .serializers import SortingGameSessionSerializer, SubmitScoreSerializer
from games.serializers import LeaderboardSerializer, TelegramIdSerializer
from drf_yasg.utils import swagger_auto_schema

from api.models import TelegramUser 

class StartSortingGameSession(APIView):
    """Создание новой игры"""
    @swagger_auto_schema(
        operation_description="Start a new StartSortingGameView",
        request_body=TelegramIdSerializer,
    )
    def post(self, request):
        serializer = TelegramIdSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        uuid = serializer.validated_data["uuid"]
        user = get_object_or_404(TelegramUser, uuid=uuid)

        game_session = SortingGameSession.objects.create(user=user)

        return Response({"message": "Игра началась", "game_id": game_session.id}, status=status.HTTP_201_CREATED)


class SubmitScore(APIView):
    """Отправка очков и обновление лидерборда"""
    @swagger_auto_schema(
        operation_description="Start a SubmitScore",
        request_body=SubmitScoreSerializer,
    )
    def post(self, request):
        serializer = SubmitScoreSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        uuid = serializer.validated_data["uuid"]
        score = serializer.validated_data["score"]

        if score is None:
            return Response({"error": "Необходимо передать 'score'"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(TelegramUser, uuid=uuid)

        game_session = SortingGameSession.objects.create(user=user, score=score)

        leaderboard_entry, created = Leaderboard.objects.get_or_create(
            user=user,
            defaults={"username": user.uuid, "score": score},
        )

        if not created:
            if score > leaderboard_entry.score:
                leaderboard_entry.score = score
                leaderboard_entry.save()

        return Response(
            {"message": "Очки сохранены", "game_id": game_session.id, "leaderboard_position": leaderboard_entry.score},
            status=status.HTTP_200_OK
        )
