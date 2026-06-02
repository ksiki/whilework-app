import logging

from django.http import HttpRequest
from ninja import Router

from .schemas import BatchRequestSchema, ErrorResponseSchema, SuccessResponseSchema
from .services import atomic_saved_messages_and_update_sources

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
def receive_raw_batch(request: HttpRequest, payload: BatchRequestSchema):
    if not payload.messages:
        return 400, {"error": "Empty batch"}

    try:
        atomic_saved_messages_and_update_sources(messages_data=payload.messages)
        return 201, {"detail": "Processed messages successfully"}

    except Exception as e:
        logger.error("Error saving batch: %s", str(e), exc_info=True)
        return 500, {"error": f"Database error: {str(e)}"}
