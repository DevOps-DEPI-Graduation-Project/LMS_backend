from datetime import timedelta
import random
import uuid
from django.db import IntegrityError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from users.serializers import (
    StudentRegisterSerializer,
    LoginSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    changePasswordSerializer
)
from users.models import PasswordResetOtp, User
from utils.apiResponse import success_response, error_response


# ============================== Student Register =============================
class StudentRegisterView(APIView):

    @swagger_auto_schema(
        request_body=StudentRegisterSerializer,
        responses={201: "Student registered successfully"}
    )
    def post(self, request):
        serializer = StudentRegisterSerializer(data=request.data)

        try:
            if serializer.is_valid():
                user = serializer.save()

                otp = str(random.randint(100000, 999999))
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save()

                try:
                    send_mail(
                        subject="Verify Your Email",
                        message=f"Your OTP is: {otp}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[user.email],
                        fail_silently=False
                    )

                except Exception as e:
                    print("Email sending failed:", e)

                return success_response(
                    message="Student registered successfully. Please verify your email.",
                    data={
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
                    status_code=status.HTTP_201_CREATED
                )

            # validation error
            field_name, first_error = list(serializer.errors.items())[0]

            if isinstance(first_error, list):
                first_error = first_error[0]

            return error_response(
                message=f"{first_error}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:
            return error_response(
                message="Email already exists",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return error_response(
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================== Verify Email =============================
class VerifyEmailView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'otp']
        )
    )
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return error_response(message="Email and OTP are required")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(message="User not found",  status_code=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return success_response(message="Email already verified")

        if not user.otp or (timezone.now() - user.otp_created_at > timedelta(minutes=10)):
            return error_response(message="OTP expired")

        if str(user.otp) != str(otp):
            return error_response(message="Invalid OTP")

        user.is_verified = True
        user.is_active = True
        user.otp = None
        user.otp_created_at = None
        user.save()

        return success_response(message="Email verified successfully")


# ============================== Resend OTP =============================
class ResendOtpView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'email': openapi.Schema(type=openapi.TYPE_STRING)},
            required=['email']
        )
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return error_response(message="Email is required")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return success_response(message="Email already verified")

        new_otp = random.randint(100000, 999999)
        user.otp = new_otp
        user.otp_created_at = timezone.now()
        user.save()

        try:
            send_mail(
                subject="Resend OTP",
                message=f"Your OTP is: {new_otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )
        except Exception:
            return error_response(message="Failed to send OTP email",  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response(message="OTP resent successfully")


# ============================== Login =============================
class UserLogin(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        try:
            if serializer.is_valid():

                user = serializer.validated_data['user_obj']
                access = serializer.validated_data['access']
                refresh = serializer.validated_data['refresh']

                return success_response(
                    message="Login successful",
                    data={
                        "tokens": {
                            "access": access,
                            "refresh": refresh
                        },
                        "user": {
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email": user.email,
                            "role": user.role,
                            "slug": user.slug,
                            "is_active": user.is_active,
                            "is_verified": user.is_verified
                        }
                    }
                )

            # validation error
            field_name, first_error = list(serializer.errors.items())[0]

            if isinstance(first_error, list):
                first_error = first_error[0]

            return error_response(
                message=f" {first_error}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            return error_response(
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ============================== Logout =============================
class UserLogout(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'refresh': openapi.Schema(type=openapi.TYPE_STRING)},
            required=['refresh']
        )
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response(message="Refresh token is required")

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logout successful")
        except TokenError:
            return error_response(message="Invalid or expired token")


# ============================== Forgot Password =============================
class ForgotPasswordView(APIView):
    @swagger_auto_schema(request_body=ForgetPasswordSerializer)
    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        otp = str(uuid.uuid4().int)[:6]
        PasswordResetOtp.objects.create(email=email, otp=otp)

        try:
            send_mail(
                subject="Resend OTP",
                message=f"Your OTP is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )
        except Exception:
            return error_response(message="Failed to send OTP email", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response(message="OTP sent to email")


# ============================== Reset Password =============================
class ResetPasswordView(APIView):
    @swagger_auto_schema(request_body=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        otp_record = serializer.validated_data['otp_record']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.save()
        otp_record.delete()

        return success_response(message="Password reset successful")


# ============================== Change Password =============================
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=changePasswordSerializer)
    def post(self, request):
        serializer = changePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(message="Password changed successfully", data=None)


# ============================== Check Token =============================
class CheckTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user:
             return error_response({
                "message": "Token not exist",
                "data": ""
            }, status=status.HTTP_401_UNAUTHORIZED)
        return success_response(
            message="Token is valid",
            data={
                "valid": True,
                "is_active": user.is_active,
                "role": user.role,
                "is_verified": getattr(user, "is_verified", False)
            }
        )