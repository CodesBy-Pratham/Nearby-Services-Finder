from django.urls import path

from .views import RegisterView, ProfileView, AssignRoleView, UserListView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view()),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/assign-role/", AssignRoleView.as_view(), name="assign-role"),
]
