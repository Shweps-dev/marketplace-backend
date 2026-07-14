from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryListView, ProductViewSet

router = DefaultRouter()
router.register("", ProductViewSet, basename="product")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("", include(router.urls)),
]
