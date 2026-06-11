import uuid

from django.db import IntegrityError

from apps.navbar.api.schemas import CreateSupportMessageRequest

from .models import SupportMessage


async def create_support_message(
    user_id: uuid.UUID, payload: CreateSupportMessageRequest
) -> bool:
    try:
        await SupportMessage.objects.acreate(
            author_id=user_id,
            title=payload.title,
            message=payload.message,
        )
        return True
    except IntegrityError:
        return False
