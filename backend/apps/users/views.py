from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .utils.auth_utils import (
    register_user,
    logout_user,
    get_profile,
    update_profile,
    refresh_access_token,
    EmailTokenObtainPairSerializer,
)


def set_auth_cookie(response, access_token, refresh_token):
    response.set_cookie(key="auth_token", value=str(access_token), httponly=True, secure=True, samesite="None", path="/")
    response.set_cookie(key="refresh_token", value=str(refresh_token), httponly=True, secure=True, samesite="None", path="/")
    return response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data, error, status_code = register_user(request)
        if error:
            return Response(error, status=status_code)
        
        response = Response({'user': data['user']}, status=status.HTTP_201_CREATED)
        return set_auth_cookie(response, data['access_token'], data['refresh_token'])


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")
            response = Response({'user': response.data.get('user')})
            return set_auth_cookie(response, access_token, refresh_token)
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data, _, _ = logout_user()
        response = Response(data)
        response.delete_cookie("auth_token", samesite="None", path="/")
        response.delete_cookie("refresh_token", samesite="None", path="/")
        return response


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data, _, _ = get_profile(request.user)
        return Response(data)

    def patch(self, request):
        data, _, _ = update_profile(request, request.user)
        return Response(data)


class RefreshAccessTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        data, error, status_code = refresh_access_token(request)
        if error:
            return Response(error, status=status_code)
        response = Response(data)
        if 'access_token' in data:
            response.set_cookie("auth_token", data['access_token'], httponly=True, secure=False, samesite="Lax", path="/")
        return response