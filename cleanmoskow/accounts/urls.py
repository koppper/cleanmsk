from django.urls import path
from .views import UserProfileView, OnboardingView, SecondOnboardingView, LoginAPIView, RegisterAPIView

urlpatterns = [
    # path("register/", RegisterUserAPIView.as_view(), name="register_user"),
    # path("login/", LoginAPIView.as_view(), name="register_user"),
    # path("auth/", AuthAPIView.as_view(), name="auth"),
    path('auth/', LoginAPIView.as_view(), name='auth-login'),
    path('register/', RegisterAPIView.as_view(), name='auth-register'),
    path("user/profile", UserProfileView.as_view(), name="get_user"),
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("onboarding-second/", SecondOnboardingView.as_view(), name="onboarding-second"),
]
