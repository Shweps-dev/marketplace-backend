from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
from apps.users.models import Address
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import CreateOrderSerializer, OrderSerializer
from .tasks import send_order_confirmation_email


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """История заказов пользователя."""
        orders = Order.objects.filter(user=request.user).prefetch_related("items", "status_history")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Создать заказ из текущей корзины.

        Процесс:
        1. Валидируем адрес доставки
        2. Проверяем корзину — не пустая, товары в наличии
        3. Создаём Order + OrderItem (снимок цен)
        4. Списываем товары со склада
        5. Очищаем корзину
        6. Запускаем Celery задачу отправки email (асинхронно!)
        """
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Проверяем адрес
        try:
            address = Address.objects.get(
                id=serializer.validated_data["shipping_address_id"],
                user=request.user
            )
        except Address.DoesNotExist:
            return Response({"error": "Address not found."}, status=404)

        # Проверяем корзину
        try:
            cart = Cart.objects.prefetch_related("items__product").get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart is empty."}, status=400)

        if not cart.items.exists():
            return Response({"error": "Cart is empty."}, status=400)

        # Проверяем наличие всех товаров
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                return Response({
                    "error": f"Not enough stock for '{item.product.name}'. Available: {item.product.stock}"
                }, status=400)

        # Всё в одной транзакции — если что-то упадёт, всё откатится
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                shipping_address=address,
                total_price=cart.total_price,
                notes=serializer.validated_data.get("notes", ""),
            )

            # Копируем товары из корзины → фиксируем цену на момент заказа
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    price_at_purchase=cart_item.product.discounted_price,
                    quantity=cart_item.quantity,
                )
                # Списываем со склада
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save(update_fields=["stock"])

            # Записываем первый статус в историю
            OrderStatusHistory.objects.create(
                order=order,
                new_status=Order.Status.PENDING,
                changed_by=request.user,
                comment="Order created",
            )

            # Очищаем корзину
            cart.items.all().delete()

        # Запускаем Celery задачу ПОСЛЕ транзакции (данные уже в БД)
        # .delay() — асинхронный запуск, не блокирует ответ
        send_order_confirmation_email.delay(order.id)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items", "status_history"
        )


class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """Отменить заказ (только если он ещё не отправлен)."""
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=404)

        if order.status in [Order.Status.SHIPPED, Order.Status.DELIVERED]:
            return Response(
                {"error": "Cannot cancel a shipped or delivered order."}, status=400
            )

        old_status = order.status
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=Order.Status.CANCELLED,
            changed_by=request.user,
            comment="Cancelled by customer",
        )

        return Response(OrderSerializer(order).data)
