from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.clients.views import ClientFavoriteCMsView, ClientMeView, ClientProfileViewSet, ClientTypeListView

router = DefaultRouter()
router.register(r"clients", ClientProfileViewSet, basename="clients")

urlpatterns = [
    path("client-types/", ClientTypeListView.as_view(), name="client-types"),
    path("clients/me/", ClientMeView.as_view(), name="client-me"),
    path("clients/me/favorite-cms/", ClientFavoriteCMsView.as_view(), name="client-favorite-cms"),
    path("", include(router.urls)),
]
