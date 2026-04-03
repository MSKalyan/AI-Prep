from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserRegistrationSerializer, UserProfileSerializer


def set_auth_cookie(response, access_token, refresh_token):

    response.set_cookie(
        key="auth_token",
        value=str(access_token),
        httponly=True,
        secure=True,
        samesite="None",
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        httponly=True,
        secure=True,
        samesite="None",
        path="/"
    )

    return response



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        access_token = refresh.access_token
        refresh_token = refresh

        response = Response({
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

        return set_auth_cookie(response, access_token, refresh_token)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise ValidationError("User account is disabled")
        User.objects.filter(id=self.user.id).update(last_activity=timezone.now())
        data["user"] = UserProfileSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):

        response = super().post(request, *args, **kwargs)

        access_token = response.data.get("access")

        if access_token:
            refresh_token = response.data.get("refresh")
            set_auth_cookie(response, access_token, refresh_token)

        # remove tokens from response body
        response.data.pop("access", None)
        response.data.pop("refresh", None)

        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        response = Response({'message': 'Successfully logged out'})
        response.delete_cookie("auth_token")
        response.delete_cookie("refresh_token")
        return response

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

class RefreshAccessTokenView(APIView):
    permission_classes = [AllowAny]

    authentication_classes = []  # Disable authentication for this view
    def post(self, request):

        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"detail": "No refresh token"}, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            new_access = refresh.access_token

            response = Response({"message": "token refreshed"})

            response.set_cookie(
                "auth_token",
                str(new_access),
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/"
            )

            return response

        except Exception:
            return Response({"detail": "Invalid refresh token"}, status=401)
