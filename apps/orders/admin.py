from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("product_name", "price_at_purchase", "quantity", "subtotal")
    extra = 0

    def subtotal(self, obj):
        return obj.subtotal


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    readonly_fields = ("old_status", "new_status", "changed_by", "comment", "changed_at")
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email",)
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ("total_price", "created_at")
