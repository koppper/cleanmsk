from django.urls import path
from .views import AdviceListByCategoryAPIView

urlpatterns = [
    path("advices/", AdviceListByCategoryAPIView.as_view(), name="advices"),
]
