from rest_framework import serializers
from .models import TelegramUser, Advice

class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ["user", "uuid", "username", "first_name", "last_name"]


class AdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = ["id", "title", "description", "image", "created_at"]
