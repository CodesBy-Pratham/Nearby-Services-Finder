from django.views.generic import TemplateView


class LoginView(TemplateView):
    template_name = "login.html"


class RegisterView(TemplateView):
    template_name = "register.html"


class HomeView(TemplateView):
    template_name = "home.html"


class ServicesView(TemplateView):
    template_name = "services.html"


class AdminPanelView(TemplateView):
    template_name = "admin_panel.html"
