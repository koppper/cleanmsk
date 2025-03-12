from rest_framework import serializers
from .models import SortingGameSession

class SortingGameSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SortingGameSession
        fields = ["id", "user", "score", "created_at"]


class SubmitScoreSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(required=True, help_text="UUID пользователя")
    score = serializers.IntegerField(required=True, help_text="score игровой сессии")

