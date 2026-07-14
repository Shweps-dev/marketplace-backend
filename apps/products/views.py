from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import ProductFilter
from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
)


class CategoryListView(generics.ListAPIView):
    """Список корневых категорий с вложенными дочерними."""
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Возвращаем только корневые категории (parent=None)
        # Дочерние подгружаются рекурсивно через get_children в сериализаторе
        return Category.objects.filter(is_active=True, parent=None).prefetch_related("children")


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Товары с фильтрацией, поиском и сортировкой.

    GET /api/v1/products/                          → список
    GET /api/v1/products/?search=iphone            → поиск
    GET /api/v1/products/?category=1&price_max=500 → фильтр
    GET /api/v1/products/?ordering=price           → сортировка
    GET /api/v1/products/{id}/                     → детали
    GET /api/v1/products/{id}/reviews/             → отзывы
    """
    permission_classes = [permissions.AllowAny]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "category__name"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", "reviews")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def reviews(self, request, slug=None):
        product = self.get_object()
        if request.method == "POST":
            serializer = ReviewSerializer(
                data=request.data,
                context={"request": request, "product_id": product.id},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=201)

        reviews = Review.objects.filter(product=product).select_related("user")
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
