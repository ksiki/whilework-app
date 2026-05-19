import uuid
from types import MappingProxyType
from typing import Any

from core.settings import SOURCE_MAX_ERRORS
from django.db import transaction

from .models import Source


def get_active_sources() -> list[Source]:
    return Source.objects.filter(is_active=True)


def update_last_parsed_message_ids(
    new_last_ids: MappingProxyType[uuid.UUID, Any],
) -> None:
    for src_id, last_id in new_last_ids.items():
        Source.objects.filter(id=src_id).update(last_parsed_id=last_id)


def register_source_error(source_id: uuid.UUID, error_message: str) -> None:
    """
    Logs a parsing error for the source.
    If the number of errors exceeds the limit, the source is deactivated.
    """

    with transaction.atomic():
        source = Source.objects.select_for_update().get(id=source_id)

        source.error_count += 1
        source.last_error_message = error_message

        if source.error_count >= SOURCE_MAX_ERRORS:
            source.is_active = False

        source.save(update_fields=["error_count", "last_error_message", "is_active"])
