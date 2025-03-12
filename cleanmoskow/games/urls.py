from django.urls import path
from .views import StartGameView, AnswerQuestionView, QuizHistoryView, LeaderboardView

urlpatterns = [
    path("start/", StartGameView.as_view()),
    path("answer/", AnswerQuestionView.as_view()),
    # path("quiz/result", QuizResultView.as_view(), name="quiz_result"),
    path("quiz/history", QuizHistoryView.as_view(), name="quiz_history"),
    path("leaderboard", LeaderboardView.as_view(), name="leaderboard"),
]
