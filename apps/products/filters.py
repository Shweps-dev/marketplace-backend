import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Фильтры для товаров.
    Позволяют запросы вида:
    /api/v1/products/?category=1&price_min=100&price_max=500&in_stock=true
    """
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(field_name="stock", method="filter_in_stock")
    category = django_filters.NumberFilter(field_name="category__id")
    has_discount = django_filters.BooleanFilter(method="filter_has_discount")

    class Meta:
        model = Product
        fields = ["category", "price_min", "price_max", "in_stock", "has_discount"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discount_percent__gt=0)
        return queryset.filter(discount_percent=0)
