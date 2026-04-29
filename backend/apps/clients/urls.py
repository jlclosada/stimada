from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.clients.views import ClientProfileViewSet, ClientTypeListView

router = DefaultRouter()
router.register(r"clients", ClientProfileViewSet, basename="clients")

urlpatterns = [
    path("client-types/", ClientTypeListView.as_view(), name="client-types"),
    path("", include(router.urls)),
]
