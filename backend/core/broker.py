import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

redis_backend = RedisAsyncResultBackend(redis_url=f"{settings.REDIS_URL}/0")
broker = AioPikaBroker(url=settings.RABBITMQ_URL).with_result_backend(redis_backend)
