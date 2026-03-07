
from datetime import timedelta
import random
import uuid
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.mail import send_mail
from cources import serializer
from users.serializers import StudentRegisterSerializer, LoginSerializer, ForgetPasswordSerializer, ResetPasswordSerializer, changePasswordSerializer
from users.models import PasswordResetOtp, User
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


#==============================student register=============================
class StudentRegisterView(APIView):
    @swagger_auto_schema(
        request_body=StudentRegisterSerializer,
        responses={201: "Student registered successfully. Please verify your email."}
    )
    def post(self, request):
        serializer = StudentRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            send_mail(
                subject="Verify Your Email",
                message=f"Your OTP is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
            )

            return Response(
                {
                    "message": "Student registered successfully. Please verify your email.",
                    "student": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "role": user.role,
                        "slug": user.slug,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
               "message": "Registration failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    
    #====================verify email==================
class VerifyEmailView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.is_verified:
            return Response({"message": "Email already verified"})

        if not user.otp or (
            timezone.now() - user.otp_created_at > timedelta(minutes=10)
        ):
            return Response({"error": "OTP expired"}, status=400)

        user.is_verified = True
        user.is_active = True
        user.otp = None
        user.otp_created_at = None
        user.save()

        return Response({"message": "Email verified successfully"})
    
        
#============login for users================= 
    
class UserLogin(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: "Login successful", 401: "Invalid credentials"}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_obj']
        access = serializer.validated_data['access']
        refresh = serializer.validated_data['refresh']

        return Response({
            "message": "Login successful",
            "access": access,
            "refresh": refresh,
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role,
                "slug": user.slug
            }
        }, status=status.HTTP_200_OK)
        
   
        # ================logout=============
        
class UserLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        

# ================== Forgot Password ==================
class ForgotPasswordView(APIView):
    @swagger_auto_schema(request_body=ForgetPasswordSerializer, responses={200: "OTP sent to email"})
    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        
        otp = str(uuid.uuid4().int)[:6]

        PasswordResetOtp.objects.create(email=email, otp=otp)

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP for password reset is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)


# ================== Reset Password ==================
class ResetPasswordView(APIView):
    # permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=ResetPasswordSerializer, responses={200: "Password reset successful"})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        otp_record = serializer.validated_data['otp_record']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        otp_record.delete()

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer=changePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)