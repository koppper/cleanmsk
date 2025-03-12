from django.urls import path
from .views import StartSortingGameSession, SubmitScore

urlpatterns = [
    path("start/", StartSortingGameSession.as_view(), name="start_game"),
    path("submit-score/", SubmitScore.as_view(), name="submit_score"),
]
