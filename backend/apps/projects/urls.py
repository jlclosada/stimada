from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.projects.views import BriefingViewSet, NotificationViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"briefings", BriefingViewSet, basename="briefings")

urlpatterns = [
    path("", include(router.urls)),
]
