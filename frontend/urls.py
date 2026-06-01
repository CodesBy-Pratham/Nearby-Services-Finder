from django.urls import path
from .views import LoginView, RegisterView, HomeView, ServicesView, AdminPanelView

urlpatterns = [
    path("", RegisterView.as_view(), name="register-redirect"),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("map/", HomeView.as_view(), name="home"),
    path("services/", ServicesView.as_view(), name="services"),
    path("admin-panel/", AdminPanelView.as_view(), name="admin-panel"),
]
