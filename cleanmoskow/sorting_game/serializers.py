from rest_framework import serializers
from .models import SortingGameSession
from accounts.models import TelegramUser
from rest_framework.generics import get_object_or_404


class SortingGameSessionSerializer(serializers.ModelSerializer):
    score = serializers.FloatField(required=True, help_text="Очки игрока")
    class Meta:
        model = SortingGameSession
        fields = ["score", "created_at", "crown"]



class SortingGameSessionHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SortingGameSession
        fields = "__all__"


