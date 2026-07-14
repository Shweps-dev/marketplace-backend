"""
Celery configuration.

Как это работает:
1. Django получает запрос на создание заказа
2. Вместо того чтобы отправлять email прямо в запросе (это медленно),
   Django кидает задачу в очередь Redis: "отправь email с этими данными"
3. Celery worker (отдельный процесс) забирает задачу из Redis и выполняет её
4. Пользователь получает ответ мгновенно, email приходит через секунду-две
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("marketplace")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находит задачи в tasks.py каждого приложения
app.autodiscover_tasks()
