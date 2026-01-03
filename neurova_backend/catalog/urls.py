from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CatalogImportView
from .views_read import PanelViewSet

router = DefaultRouter()
router.register(r"panels", PanelViewSet, basename="panels")

urlpatterns = [
    path("catalog/import/", CatalogImportView.as_view()),
    path("", include(router.urls)),
]
