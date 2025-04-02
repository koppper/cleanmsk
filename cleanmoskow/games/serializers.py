from rest_framework import serializers
from .models import QuizQuestions, Leaderboard, GameSession


class QuizQuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestions
        fields = ["id", "question", "answers", "image"]


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = "__all__"
        

class GameSessionSerializer(serializers.ModelSerializer):
    questions = QuizQuestionsSerializer(many=True)
    
    class Meta:
        model = GameSession
        fields = "__all__"


class AnswerQuestionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=True, help_text="ID игровой сессии")
    question_id = serializers.IntegerField(required=True, help_text="ID вопроса, на который даётся ответ")
    answer = serializers.IntegerField(allow_null=True, required=False, help_text="Выбранный вариант ответа (индекс)")


class TelegramIdSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(required=True, help_text="UUID пользователя")


class GameResultSerializer(serializers.ModelSerializer):
    """Сериализатор результата квиза"""
    result = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = ["correct_answers", "total_questions", "result"]

    def get_result(self, obj):
        """Формула оценки результата"""
        percentage = (obj.correct_answers / obj.total_questions) * 100
        if percentage < 50:
            return "Плохо"
        elif percentage < 80:
            return "Хорошо"
        return "Отлично"


class GameHistorySerializer(serializers.ModelSerializer):
    """Сериализатор истории игр"""
    result = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")

    class Meta:
        model = GameSession
        fields = ["date", "correct_answers", "total_questions", "result"]

    def get_result(self, obj):
        return GameResultSerializer().get_result(obj)


# class LeaderboardSerializer(serializers.ModelSerializer):
#     """Сериализатор рейтинга"""
#     username = serializers.CharField(source="user.username")

#     class Meta:
#         model = Leaderboard
#         fields = ["username", "score"]


