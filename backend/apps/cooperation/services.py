from apps.cooperation.api.schemas import CreateMessageRequest

from .models import Message


async def process_cooperation_offer(payload: CreateMessageRequest) -> Message:
    message_obj = await Message.objects.acreate(
        name=payload.name,
        email=payload.email,
        text=payload.message,
    )

    return message_obj
