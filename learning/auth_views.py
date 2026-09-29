from django.conf import settings
from django.contrib.auth.views import LoginView


class CereqoLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "demo_username": settings.DEMO_LOGIN_USERNAME,
                "demo_password": settings.DEMO_LOGIN_PASSWORD,
            }
        )
        return context
