import uuid
from types import MappingProxyType
from typing import Any

from core.settings import SOURCE_MAX_ERRORS
from django.db import transaction
from django.db.models import Prefetch

from .models import Source, SourceTopic


def get_active_sources() -> list[Source]:
    active_topics_prefetch = Prefetch(
        "topics",
        queryset=SourceTopic.objects.filter(is_active=True),
        to_attr="active_topics",
    )

    return list(
        Source.objects.filter(is_active=True).prefetch_related(active_topics_prefetch)
    )


def get_source_types() -> list[str]:
    return Source.Platform.choices


def update_last_parsed_message_ids(
    source_updates: MappingProxyType[uuid.UUID, Any]
    | dict[uuid.UUID, Any]
    | None = None,
    topic_updates: MappingProxyType[uuid.UUID, Any]
    | dict[uuid.UUID, Any]
    | None = None,
) -> None:
    if source_updates:
        for src_id, last_id in source_updates.items():
            Source.objects.filter(id=src_id).update(last_parsed_id=last_id)

    if topic_updates:
        for topic_id, last_id in topic_updates.items():
            SourceTopic.objects.filter(id=topic_id).update(last_parsed_id=last_id)


def register_parsing_error(
    target_id: uuid.UUID, error_message: str, is_topic: bool = False
) -> None:
    """
    Logs a parsing error for the source.
    If the number of errors exceeds the limit, the source is deactivated.
    """
    model = SourceTopic if is_topic else Source

    with transaction.atomic():
        target = model.objects.select_for_update().get(id=target_id)

        target.error_count += 1
        target.last_error_message = error_message

        if target.error_count >= SOURCE_MAX_ERRORS:
            target.is_active = False

        target.save(update_fields=["error_count", "last_error_message", "is_active"])
