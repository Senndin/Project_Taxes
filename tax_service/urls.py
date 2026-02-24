from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, ImportJobViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"imports", ImportJobViewSet, basename="import")

urlpatterns = [
    path("", include(router.urls)),
]
