from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RefreshAccessTokenView, RegisterView, LoginView, LogoutView, UserProfileView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path("refresh/", RefreshAccessTokenView.as_view(), name="refresh"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
