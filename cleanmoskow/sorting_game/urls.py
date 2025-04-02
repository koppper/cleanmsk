from django.urls import path
from .views import StartSortingGameSession, SortingGameHistory, StartSortingGame

urlpatterns = [
    path("create/", StartSortingGameSession.as_view(), name="create_game"),
    path("history/", SortingGameHistory.as_view(), name="game_history"),
    path("start/", StartSortingGame.as_view(), name="start_game"),
]
