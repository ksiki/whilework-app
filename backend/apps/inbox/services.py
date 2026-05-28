import uuid
from types import MappingProxyType
from typing import Any, NamedTuple

from django.db import transaction

import apps.sources.services as sources_services

from .models import ParserRawMessage


class ParseResult(NamedTuple):
    instances: list[ParserRawMessage]
    latest_source_ids: MappingProxyType[uuid.UUID, Any]
    latest_topic_ids: MappingProxyType[uuid.UUID, Any]


def _create_object_list_and_search_last_ids(messages_data: list[dict]) -> ParseResult:
    """
    Returns ParseResult(NamedTuple) consisting of instances and split dictionaries
    for updating source and topic cursors.
    """
    instances = []
    latest_source_ids = {}
    latest_topic_ids = {}

    for msg in messages_data:
        source_id = msg.get("source_id")
        topic_id = msg.get("topic_id")
        external_msg_id = msg.get("external_msg_id")

        instances.append(
            ParserRawMessage(
                source_id=source_id,
                topic_id=topic_id,
                external_msg_id=external_msg_id,
                raw_text=msg.get("raw_text"),
                metadata=msg.get("metadata", {}),
            )
        )
        if topic_id:
            latest_topic_ids[topic_id] = external_msg_id
        else:
            latest_source_ids[source_id] = external_msg_id

    return ParseResult(
        instances=instances,
        latest_source_ids=MappingProxyType(latest_source_ids),
        latest_topic_ids=MappingProxyType(latest_topic_ids),
    )


def atomic_saved_messages_and_update_sources(messages_data: list[dict]) -> None:
    """
    Atomically uploads all dirty messages to the database and updates the id
    of the last message in the sources or topics.
    """
    parse_result = _create_object_list_and_search_last_ids(messages_data=messages_data)

    with transaction.atomic():
        ParserRawMessage.objects.bulk_create(
            parse_result.instances, batch_size=100, ignore_conflicts=True
        )
        sources_services.update_last_parsed_message_ids(
            source_updates=parse_result.latest_source_ids,
            topic_updates=parse_result.latest_topic_ids,
        )
