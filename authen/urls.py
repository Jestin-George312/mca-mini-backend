# authn/urls.py
"""
from django.urls import path
from .views import RegisterView,hello_world
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('signup/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),  # JWT login
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('hello/', hello_world),
]
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView





#from .views import SendOtpView, VerifyOtpAndResetPasswordView
from .views import (
    SignupView,
    VerifySignupOtpView,
    SendOtpView,
    VerifyOtpAndResetPasswordView,
    TokenRefreshView,
    UpdateUserProfileView,
    GetUserProfileView
)



urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("verify-signup-otp/", VerifySignupOtpView.as_view(), name="verify_signup_otp"),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("send-otp/", SendOtpView.as_view(), name="send_otp"),
    path("verify-otp/", VerifyOtpAndResetPasswordView.as_view(), name="verify_otp"),


    path("update-profile/", UpdateUserProfileView.as_view(), name="update_profile"),
    
    # <-- 2. Add this new URL pattern -->
    path("profile/", GetUserProfileView.as_view(), name="get_profile"),
]
