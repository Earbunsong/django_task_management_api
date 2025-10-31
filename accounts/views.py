from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class AllowAnyForAuth(permissions.AllowAny):
    pass


class RegisterView(APIView):
    permission_classes = [AllowAnyForAuth]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # TODO: send verification email with token
        return Response({"message": "Registered successfully. Please verify your email.", "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAnyForAuth]

    def get(self, request, token: str):
        # TODO: verify token and activate user
        return Response({"message": "Email verified (stub)."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        # With JWT this is typically handled client-side or via blacklist; stubbed
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAnyForAuth]

    def post(self, request):
        # TODO: send reset link
        return Response({"message": "Password reset link sent (stub)."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAnyForAuth]

    def post(self, request):
        # TODO: reset password using token
        return Response({"message": "Password reset successful (stub)."})


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminDisableUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk: int):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.is_disabled = True
        user.is_active = False
        user.save(update_fields=["is_disabled", "is_active"])
        return Response({"message": "User disabled"}, status=status.HTTP_200_OK)
