from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product
from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartSerializer


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_or_create_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def get(self, request):
        """Получить корзину текущего пользователя."""
        cart = self._get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        """
        Добавить товар в корзину.
        Если товар уже в корзине — увеличить количество.
        """
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=404)

        if product.stock < quantity:
            return Response({"error": f"Only {product.stock} items in stock."}, status=400)

        cart = self._get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

        return Response(CartSerializer(cart).data, status=201 if created else 200)

    def delete(self, request):
        """Очистить всю корзину."""
        cart = self._get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared."})


class CartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id):
        """Изменить количество конкретного товара в корзине."""
        quantity = request.data.get("quantity")
        if not quantity or int(quantity) < 1:
            return Response({"error": "Quantity must be at least 1."}, status=400)

        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found."}, status=404)

        if item.product.stock < int(quantity):
            return Response({"error": f"Only {item.product.stock} in stock."}, status=400)

        item.quantity = int(quantity)
        item.save()
        return Response(CartSerializer(item.cart).data)

    def delete(self, request, item_id):
        """Удалить конкретный товар из корзины."""
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found."}, status=404)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
