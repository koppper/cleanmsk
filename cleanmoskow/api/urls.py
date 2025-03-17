from django.urls import path
from .views import AdviceListAPIView

urlpatterns = [
    path("advices/", AdviceListAPIView.as_view(), name="advices"),
]
