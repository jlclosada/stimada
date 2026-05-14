from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content_makers.views import ContentMakerMeView, ContentMakerViewSet

router = DefaultRouter()
router.register(r"content-makers", ContentMakerViewSet, basename="content-makers")

urlpatterns = [
    path("content-makers/me/", ContentMakerMeView.as_view(), name="content-maker-me"),
    path("", include(router.urls)),
]
