from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content_makers.views import ContentMakerViewSet

router = DefaultRouter()
router.register(r"content-makers", ContentMakerViewSet, basename="content-makers")

urlpatterns = [
    path("", include(router.urls)),
]
