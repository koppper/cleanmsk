from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import QuizQuestions, GameSession, Leaderboard
from api.models import TelegramUser
from .serializers import QuizQuestionsSerializer, LeaderboardSerializer, GameResultSerializer, AnswerQuestionSerializer, GameHistorySerializer, TelegramIdSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema


class StartGameView(APIView):
    """Создаёт новую игровую сессию и выдаёт первый вопрос"""

    # permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Start a new session",
        request_body=TelegramIdSerializer,
    )
    def post(self, request):
        serializer = TelegramIdSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        uuid = serializer.validated_data["uuid"]
        user = get_object_or_404(TelegramUser, uuid=uuid)


        questions = QuizQuestions.objects.order_by("?")[:5]

        # serializer = QuizQuestionsSerializer(data=request.data)
        questions_data = QuizQuestionsSerializer(questions, many=True).data
        # if questions_data.is_valid():

        session = GameSession.objects.create(
            user=user,
            questions=questions_data,
            current_question_index=0,
            correct_answers=0,
            total_questions=len(questions_data),
            finished=False,
            created_at=None
        )
        return Response({
            "session_id": session.id,
            "user": user.uuid,
            "question": questions_data[0]
        })

class AnswerQuestionView(APIView):
    """Проверяет ответ на конкретный вопрос, обновляет игровую сессию"""

    @swagger_auto_schema(
        operation_description="Ответ на вопрос викторины",
        request_body=AnswerQuestionSerializer,
        responses={
            200: AnswerQuestionSerializer,
            400: "Некорректные данные.",
            404: "Игровая сессия или вопрос не найдены."
        }
    )
    def post(self, request):
        
        serializer = AnswerQuestionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        uuid = serializer.validated_data["uuid"]
        session_id = serializer.validated_data["session_id"]
        question_id = serializer.validated_data["question_id"]
        answer = serializer.validated_data["answer"]
        user = get_object_or_404(TelegramUser, uuid=uuid)  # Находим пользователя по Telegram ID
        print(f"Telegram id: {uuid} {user} {user.id}")

        print(f"🔹 Получен ответ: session_id={session_id}, question_id={question_id}, answer={answer}")

        session = get_object_or_404(GameSession, id=session_id, finished=False)

        current_question = session.questions[session.current_question_index]
        current_question_id = current_question["id"]

        if question_id != current_question_id:
            return Response({
                "error": "Вы должны ответить на текущий вопрос, прежде чем переходить к следующему.",
                "current_question_id": current_question_id
            }, status=status.HTTP_400_BAD_REQUEST)

        if question_id in session.answered_questions:
            return Response({
                "error": "Вы уже отвечали на этот вопрос.",
                "current_question_id": current_question_id
            }, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(QuizQuestions, id=question_id)
        is_correct = answer == question.correct_answer
        explanation = question.explanation

        if is_correct:
            session.correct_answers += 1

        session.answered_questions.append(question_id)
        session.current_question_index += 1
        session.save()

        if session.current_question_index >= session.total_questions:
            session.finished = True

            # Начисление баллов
            score = session.correct_answers * 5 + 10

            # Корректный расчёт результата
            percentage = (session.correct_answers / session.total_questions) * 100
            if percentage < 50:
                result = "Плохой"
            elif percentage < 80:
                result = "Хорошо"
            else:
                result = "Отлично"

            leaderboard_entry, created = Leaderboard.objects.get_or_create(
                user=session.user,
                defaults={"username": session.user.uuid, "score": 0}
            )
            
            leaderboard_entry.score += score  # Обновляем общий счет
            leaderboard_entry.save()
            session.save()

            return Response({
                "correct": is_correct,
                "game_over": True,
                "score": session.correct_answers * 5,
                "total_questions": session.total_questions,
                "result": result,
                "total_score": leaderboard_entry.score,
                **({"explanation": explanation} if explanation else {})
            }, status=status.HTTP_200_OK)

        next_question = session.questions[session.current_question_index]
        current_score = session.correct_answers * 5  # Текущий счет пользователя

        return Response({
            "correct": is_correct,
            "game_over": False,
            "question": next_question,
            "current_score": current_score,

            **({"explanation": explanation} if explanation else {})
        }, status=status.HTTP_200_OK)


class QuizHistoryView(APIView):
    """Получить историю завершенных игр пользователя"""
    @swagger_auto_schema(
        query_serializer=TelegramIdSerializer,
    )
    def get(self, request):
        serializer = TelegramIdSerializer(data=request.query_params)  # Берем данные из query_params
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        uuid = serializer.validated_data["uuid"]
        user = get_object_or_404(TelegramUser, uuid=uuid)  # Находим пользователя по Telegram ID

        sessions = GameSession.objects.filter(user=user, finished=True).order_by("-created_at")

        if not sessions.exists():
            return Response({"error": "Нет завершенных игр"}, status=status.HTTP_404_NOT_FOUND)

        total_score = Leaderboard.objects.filter(user=user).first()
        total_score = total_score.score if total_score else 0

        return Response({
            "total_score": total_score,
            "games": GameHistorySerializer(sessions, many=True).data
        }, status=status.HTTP_200_OK)


class LeaderboardView(APIView):
    """Получить топ игроков с местами и текущим местом пользователя"""
    @swagger_auto_schema(
        query_serializer=TelegramIdSerializer,
        )
    def get(self, request):
        serializer = TelegramIdSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        uuid = serializer.validated_data["uuid"]
        user = get_object_or_404(TelegramUser, uuid=uuid)

        leaderboard = Leaderboard.objects.order_by("-score").values("user", "score")

        if not leaderboard:
            return Response({"error": "Нет данных в лидерборде"}, status=status.HTTP_404_NOT_FOUND)

        user_ids = [entry["user"] for entry in leaderboard]
        users = TelegramUser.objects.filter(id__in=user_ids)
        user_dict = {u.id: u.username for u in users}

        ranked_players = [
            {
                "place": index + 1,
                "username": user_dict.get(entry["user"], "Unknown"),  # Берём имя пользователя
                "score": entry["score"]
            }
            for index, entry in enumerate(leaderboard)
        ]

        # Находим место текущего пользователя
        user_rank = next((player["place"] for player in ranked_players if player["username"] == user.username), None)

        return Response({
            "top_players": ranked_players[:10],
            "user_rank": user_rank
        }, status=status.HTTP_200_OK)
