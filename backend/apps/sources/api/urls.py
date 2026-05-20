# sources/api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SourceAPIViewSet

router = DefaultRouter()
router.register(r"", SourceAPIViewSet, basename="source")

urlpatterns = [
    path("", include(router.urls)),
]
