import logging

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja import Router

from apps.inbox.services import atomic_saved_messages_and_update_sources
from apps.inbox.tasks import process_pending_messages_task

from .schemas import BatchRequestSchema, ErrorResponseSchema, SuccessResponseSchema

logger = logging.getLogger(__name__)

router = Router(tags=["Inbox Batch"])


@router.post(
    "/batch/",
    response={
        201: SuccessResponseSchema,
        400: ErrorResponseSchema,
        500: ErrorResponseSchema,
    },
    summary="Process a raw batch of messages",
)
async def receive_raw_batch(request: HttpRequest, payload: BatchRequestSchema):
    if not payload.messages:
        return 400, {"error": "Empty batch"}

    try:
        await sync_to_async(
            atomic_saved_messages_and_update_sources, thread_sensitive=True
        )(messages_data=payload.messages)

        await process_pending_messages_task.kiq(count=len(payload.messages))

        return 201, {"detail": "Processed messages successfully"}
    except Exception as e:
        logger.error("Error saving batch: %s", str(e), exc_info=True)
        return 500, {"error": f"Database error: {str(e)}"}
