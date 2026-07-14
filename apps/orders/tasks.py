from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """
    Celery задача: отправляет email с подтверждением заказа.

    bind=True — задача знает о себе (можно retry)
    max_retries=3 — при ошибке повторяет 3 раза
    default_retry_delay=60 — ждёт 60 секунд перед повтором

    Эта задача выполняется в отдельном процессе (Celery worker),
    поэтому пользователь не ждёт отправки email.
    """
    try:
        from .models import Order
        order = Order.objects.select_related("user").prefetch_related("items").get(id=order_id)

        items_text = "\n".join(
            f"  - {item.product_name} x{item.quantity} = ${item.subtotal:.2f}"
            for item in order.items.all()
        )

        message = f"""
Hello {order.user.username}!

Your order #{order.id} has been confirmed.

Items:
{items_text}

Total: ${order.total_price:.2f}

Status: {order.get_status_display()}

Thank you for shopping with us!
        """.strip()

        send_mail(
            subject=f"Order #{order.id} Confirmed — Marketplace",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )

        logger.info(f"Order confirmation email sent for order #{order_id}")
        return f"Email sent for order #{order_id}"

    except Exception as exc:
        logger.error(f"Failed to send email for order #{order_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_status_update_email(order_id: int, new_status: str):
    """Уведомление об изменении статуса заказа."""
    try:
        from .models import Order
        order = Order.objects.select_related("user").get(id=order_id)

        send_mail(
            subject=f"Order #{order.id} Status Update",
            message=f"Your order #{order.id} status changed to: {new_status.upper()}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Status update email failed: {e}")
