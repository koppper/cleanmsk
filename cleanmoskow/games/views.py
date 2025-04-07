from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import QuizQuestions, GameSession, Leaderboard, CensoredWord
from accounts.models import TelegramUser
from .serializers import QuizQuestionsSerializer, LeaderboardSerializer, GameResultSerializer, AnswerQuestionSerializer, GameHistorySerializer, TelegramIdSerializer
from django.contrib.auth import get_user_model
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
import logging
from accounts.utils import log_user_action


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class StartGameView(APIView):
    """Создаёт новую игровую сессию и выдаёт первый вопрос"""
    # authentication_classes = [] 

    # permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Start a new session",
    )
    def post(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)
        log_user_action(request, "quiz_start")

        telegram_user = request.user.telegram_profile
        already_answered_ids = telegram_user.answered_questions_ids or []
        available_questions = QuizQuestions.objects.exclude(id__in=already_answered_ids)

        # questions = QuizQuestions.objects.order_by("?")[:5]
        # Если осталось меньше 5 — просто берём любые 5 случайных из всей базы
        if available_questions.count() < 5:
            questions = QuizQuestions.objects.order_by("?")[:5]
            telegram_user.answered_questions_ids = []
        else:
            questions = available_questions.order_by("?")[:5]
        questions_data = QuizQuestionsSerializer(questions, many=True).data

        session = GameSession.objects.create(
            user=telegram_user,
            questions=questions_data,
            current_question_index=0,
            correct_answers=0,
            total_questions=len(questions_data),
            finished=False,
            created_at=None
        )
        return Response({
            "session_id": session.id,
            "user": telegram_user.uuid,
            "question": questions_data[0]
        })


@method_decorator(csrf_exempt, name='dispatch')
class AnswerQuestionView(APIView):
    """Проверяет ответ на конкретный вопрос, обновляет игровую сессию"""
    # authentication_classes = [] 

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
        session_id = serializer.validated_data["session_id"]
        question_id = serializer.validated_data["question_id"]
        answer = serializer.validated_data["answer"]

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
        is_correct = answer is not None and answer == question.correct_answer
        explanation = question.explanation
        leaderboard_entry, created = Leaderboard.objects.get_or_create(
            user=session.user,
            defaults={"score": 0}
        )
        question.total_answers += 1

        if is_correct:
            session.correct_answers += 1
            question.correct_answers += 1
            leaderboard_entry.score += 5
        question.save()

        telegram_user = session.user

        if question_id not in telegram_user.answered_questions_ids:
            telegram_user.answered_questions_ids.append(question_id)
            telegram_user.save()
    
        session.answered_questions.append(question_id)
        session.current_question_index += 1
        leaderboard_entry.save()

        session.save()

        if session.current_question_index >= session.total_questions:
            session.finished = True

            # score = session.correct_answers * 5 + 10
            logger.info(f"sesssion total questions: {session.correct_answers} {session.total_questions}" )
            percentage = (session.correct_answers / session.total_questions) * 100
            if percentage < 50:
                result = "Плохо"
            elif percentage < 80:
                result = "Хорошо"
            else:
                result = "Отлично"
            
            leaderboard_entry.score += 10

            leaderboard_entry.save()
            session.save()
            total_score = (session.correct_answers * 5) + 10
            return Response({
                "correct": is_correct,
                "game_over": True,
                # "score": session.correct_answers * 5,
                "total_questions": session.total_questions,
                "result": result,
                "total_score": total_score,
                "correct_answer": question.correct_answer,

                **({"explanation": explanation} if explanation else {})
            }, status=status.HTTP_200_OK)

        next_question = session.questions[session.current_question_index]
        current_score = session.correct_answers * 5

        return Response({
            "correct": is_correct,
            "game_over": False,
            "question": next_question,
            "current_score": current_score,
            "correct_answer": question.correct_answer,

            **({"explanation": explanation} if explanation else {})
        }, status=status.HTTP_200_OK)


class QuizHistoryView(APIView):
    """Получить историю всех игр пользователя"""

    def get(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)

        telegram_user = request.user.telegram_profile

        sessions = GameSession.objects.filter(user=telegram_user).order_by("-created_at")

        if not sessions.exists():
            return Response({"error": "Нет завершенных игр"}, status=status.HTTP_404_NOT_FOUND)

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
            "games": GameHistorySerializer(sessions, many=True).data
        }, status=status.HTTP_200_OK)


class LeaderboardView(APIView):
    """Получить топ игроков с местами и текущим местом пользователя"""

    def get(self, request):
        if not request.user or not hasattr(request.user, "telegram_profile"):
            return Response({"error": "Пользователь не авторизован"}, status=401)

        telegram_user = request.user.telegram_profile

        top_players = (
            Leaderboard.objects.select_related("user")
            .order_by("-score")
        )

        user_score = Leaderboard.objects.filter(user=telegram_user).values_list("score", flat=True).first() or 0
        user_rank = (
            Leaderboard.objects.filter(score__gt=user_score).count() + 1
        ) if user_score else None

        ranked_players = [
            {
                "place": index + 1,
                "username": entry.user.username if entry.user else "Unknown",
                "score": entry.score

            }
            for index, entry in enumerate(top_players)
        ]

        return Response({
            "players": ranked_players,
            "user_rank": user_rank,
            "score": user_score,
        }, status=status.HTTP_200_OK)
