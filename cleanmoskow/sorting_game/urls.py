from django.urls import path
from .views import StartSortingGameSession, SortingGameHistory

urlpatterns = [
    path("start/", StartSortingGameSession.as_view(), name="start_game"),
    path("history/", SortingGameHistory.as_view(), name="start_game"),
]
