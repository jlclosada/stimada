from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordResetRequestListView,
    PasswordResetRequestView,
    PasswordResetResolveView,
    RefreshView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

auth_urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password-reset/requests/", PasswordResetRequestListView.as_view(), name="auth-reset-list"),
    path("password-reset/requests/<int:pk>/resolve/", PasswordResetResolveView.as_view(), name="auth-reset-resolve"),
]

urlpatterns = [
    path("auth/", include(auth_urlpatterns)),
    path("", include(router.urls)),
]
