from rest_framework import serializers
from .models import SortingGameSession
from accounts.models import TelegramUser
from rest_framework.generics import get_object_or_404


class SortingGameSessionSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(write_only=True, required=True, help_text="UUID пользователя")
    score = serializers.FloatField(required=True, help_text="Очки игрока")

    class Meta:
        model = SortingGameSession
        fields = ["uuid", "score", "created_at"]

    def create(self, validated_data):
        """Создание новой игровой сессии"""
        uuid = validated_data.pop("uuid")
        user = get_object_or_404(TelegramUser, uuid=uuid)
        return SortingGameSession.objects.create(user=user, **validated_data)


class SortingGameSessionHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SortingGameSession
        fields = "__all__"


