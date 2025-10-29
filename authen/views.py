# authn/views.py
"""from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def hello_world(request):
    return Response({"message": "Hello from Django!"})



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)"""


#from django.shortcuts import render

# Create your views here.
# views.py
import random
import string
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.timezone import now
from .models import UserProfile 
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework import status
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create a RefreshToken instance from the provided refresh token
            refresh = RefreshToken(refresh_token)
            # Generate a new access token
            new_access_token = str(refresh.access_token)
            return Response({"access": new_access_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)


class SendOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            # Generate a 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))
            expiry_time = now() + timedelta(minutes=5)  # OTP expires in 5 minutes

            # Save OTP in the UserProfile model
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.otp = otp
            profile.otp_expiry = expiry_time
            profile.save()

            try:
                send_mail(
                    "Password Reset OTP",
                    f"Your OTP for Password Reset is : {otp}",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
                return Response({"message":"OTP sent successfully"},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":"User with this email does not exist"},status=status.HTTP_404_NOT_FOUND)



class VerifyOtpAndResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        profile = UserProfile.objects.filter(user=user).first()
        if not profile or profile.otp != otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if profile.otp_expiry < now():
            return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        profile.otp = None  # Clear the OTP after successful reset
        profile.otp_expiry = None
        profile.save()

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)    
    
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        # Create user but keep inactive until OTP verification
        user = User.objects.create(username=username, email=email, password=make_password(password))
        user.is_active = True
        user.save()
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Generate OTP
        """
        otp = ''.join(random.choices(string.digits, k=6))
        expiry_time = now() + timedelta(minutes=10)

        # Save OTP in UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.otp = otp
        profile.otp_expiry = expiry_time
        profile.save()

        # Send OTP via email
        send_mail(
            "Signup OTP Verification",
            f"Your OTP for signup verification is: {otp}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )"""

        return Response({"message": "User registered. OTP sent to email for verification.",
             "refresh": str(refresh),
            "access": str(access),
                         }, status=status.HTTP_201_CREATED)


class VerifySignupOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        profile = UserProfile.objects.filter(user=user).first()
        if not profile or profile.otp != otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if profile.otp_expiry < now():
            return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Activate user after OTP verification
        user.is_active = True
        user.save()

        # Clear OTP after successful verification
        profile.otp = None
        profile.otp_expiry = None
        profile.save()

        return Response({"message": "Signup successful. OTP verified!"}, status=status.HTTP_200_OK)


class UpdateUserProfileView(APIView):
    """
    View to update user's email, password, and name.
    User must be authenticated.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        data = request.data

        # Handle email update (no change)
        if 'email' in data:
            new_email = data['email']
            if not new_email:
                return Response({"error": "Email cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                return Response({"error": "This email is already in use."}, status=status.HTTP_400_BAD_REQUEST)
            user.email = new_email

        # Handle password update (no change)
        if 'password' in data:
            new_password = data['password']
            if not new_password:
                 return Response({"error": "Password cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)

        # --- ADD THIS SECTION ---
        # Handle name update
        if 'name' in data:
            full_name = data['name'].strip().split(' ', 1)
            user.first_name = full_name[0]
            if len(full_name) > 1:
                user.last_name = full_name[1]
            else:
                user.last_name = "" # Clear last name if only first name is provided
        # --- END OF ADDED SECTION ---

        # Save the changes
        try:
            user.save()
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)


class GetUserProfileView(APIView):
    """
    View to get the current authenticated user's profile data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Combine first_name and last_name into a single 'name' field
        # to match what your frontend expects.
        full_name = f"{user.first_name} {user.last_name}".strip()

        return Response({
            "username": user.username,
            "email": user.email,
            "name": full_name if full_name else user.username, # Fallback to username
        }, status=status.HTTP_200_OK)