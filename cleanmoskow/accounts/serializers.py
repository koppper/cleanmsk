from rest_framework import serializers
from .models import TelegramUser
from oauth2_provider.models import AccessToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ["user", "uuid", "username", "first_name", "last_name"]


class LoginSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField(required=True, help_text="telegram_id пользователя")


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="username пользователя")
    telegram_id = serializers.IntegerField(required=True, help_text="telegram_id пользователя")


class LogoutSerializer(serializers.Serializer):
    token = serializers.CharField()