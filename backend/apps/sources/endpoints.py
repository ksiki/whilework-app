import uuid
from typing import List

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.sources import services
from apps.sources.models import Source, SourceTopic

from .schemas import (
    ErrorResponseSchema,
    MessageResponseSchema,
    ReportErrorInSchema,
    SourceSchema,
)

router = Router(tags=["Sources"])


@router.get("/", response=List[SourceSchema])
def list_sources(request: HttpRequest):
    return services.get_active_sources()


@router.get("/{source_id}/", response=SourceSchema)
def retrieve_source(request: HttpRequest, source_id: uuid.UUID):
    return get_object_or_404(services.get_active_sources(), id=source_id)


@router.post(
    "/{source_id}/report-error/",
    response={
        200: MessageResponseSchema,
        404: ErrorResponseSchema,
    },
)
def report_error(
    request: HttpRequest,
    source_id: uuid.UUID,
    payload: ReportErrorInSchema,
):
    try:
        if payload.topic_id:
            services.register_parsing_error(
                target_id=payload.topic_id,
                error_message=payload.error_message,
                is_topic=True,
            )
        else:
            services.register_parsing_error(
                target_id=source_id,
                error_message=payload.error_message,
                is_topic=False,
            )
        return 200, {"detail": "Error reported"}

    except (Source.DoesNotExist, SourceTopic.DoesNotExist):
        return 404, {"error": "Target not found"}
