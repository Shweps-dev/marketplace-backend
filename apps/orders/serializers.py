from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "price_at_purchase", "quantity", "subtotal")


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ("old_status", "new_status", "changed_by_email", "comment", "changed_at")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "status", "status_display", "total_price",
            "shipping_address", "notes", "items",
            "status_history", "created_at",
        )
        read_only_fields = ("id", "total_price", "status", "created_at")


class CreateOrderSerializer(serializers.Serializer):
    """Для создания заказа нужен только адрес и опциональные заметки."""
    shipping_address_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
