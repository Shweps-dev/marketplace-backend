from django.db import models
from apps.users.models import User, Address
from apps.products.models import Product


class Order(models.Model):
    """
    Заказ. При создании:
    1. Товары копируются из корзины в OrderItem (снимок цены на момент заказа)
    2. Celery отправляет email с подтверждением
    3. История статусов пишется в OrderStatusHistory
    """
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    shipping_address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.user.email} ({self.status})"


class OrderItem(models.Model):
    """
    Позиция заказа — снимок товара на момент покупки.
    Цена фиксируется при создании заказа, чтобы изменение
    цены товара не влияло на уже оформленные заказы.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)   # Сохраняем название на случай удаления товара
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        db_table = "order_items"

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class OrderStatusHistory(models.Model):
    """
    История изменений статуса заказа.
    Позволяет видеть когда и кем был изменён статус.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_history"
        ordering = ["-changed_at"]
