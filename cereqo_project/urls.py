from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

from learning.auth_views import CereqoLoginView

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/cereqo/img/cereqo-logo.png", permanent=True)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("accounts/login/", CereqoLoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("", include("learning.urls")),
]
