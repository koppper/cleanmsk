from django.urls import path
from .views import RegisterUserAPIView, GetUserAPIView, AdviceListAPIView

urlpatterns = [
    path("register/", RegisterUserAPIView.as_view(), name="register_user"),
    path("user/<str:uuid>/", GetUserAPIView.as_view(), name="get_user"),
    path("advices/", AdviceListAPIView.as_view(), name="advices"),

]
