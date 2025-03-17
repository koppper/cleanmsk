from django.urls import path
from .views import AuthAPIView, UserProfileView, OnboardingView, SecondOnboardingView

urlpatterns = [
    # path("register/", RegisterUserAPIView.as_view(), name="register_user"),
    # path("login/", LoginAPIView.as_view(), name="register_user"),
    path("auth/", AuthAPIView.as_view(), name="auth"),

    path("user/profile", UserProfileView.as_view(), name="get_user"),
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("onboarding-second/", SecondOnboardingView.as_view(), name="onboarding-second"),
]
