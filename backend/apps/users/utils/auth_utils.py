from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import User
from ..serializers import UserRegistrationSerializer, UserProfileSerializer


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


def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    refresh_token = refresh

    return {
        'user': UserProfileSerializer(user).data,
        'access_token': str(access_token),
        'refresh_token': str(refresh_token),
    }, None, None


def logout_user():
    return {'message': 'Successfully logged out'}, None, None


def get_profile(user):
    return UserProfileSerializer(user).data, None, None


def update_profile(request, user):
    serializer = UserProfileSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return serializer.data, None, None


def refresh_access_token(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return None, {"detail": "No refresh token"}, 401

    from rest_framework_simplejwt.exceptions import TokenError
    try:
        refresh = RefreshToken(refresh_token)
        new_access = refresh.access_token

        return {"message": "token refreshed", "access_token": str(new_access)}, None, None
    except TokenError:
        return None, {"detail": "Invalid refresh token"}, 401


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise ValidationError("User account is disabled")
        User.objects.filter(id=self.user.id).update(last_activity=timezone.now())
        data["user"] = UserProfileSerializer(self.user).data
        return data