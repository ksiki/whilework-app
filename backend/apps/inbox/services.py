import uuid
from types import MappingProxyType
from typing import Any, NamedTuple

from django.db import transaction

import apps.sources.services as sources_services

from .models import ParserRawMessage


class ParseResult(NamedTuple):
    instances: list[ParserRawMessage]
    latest_parsed_ids: MappingProxyType[uuid.UUID, Any]


def _create_object_list_and_search_last_ids(messages_data: list) -> ParseResult:
    """
    Reurned ParseResult(NamedTuple) consist of instances(list[ParserRawMessage]) and latest_parsed_ids(MappingProxyType[uuid.UUID, Any])
    """

    instances = []
    latest_parsed_ids = {}

    for msg in messages_data:
        source_id = msg.get("source_id")
        external_msg_id = msg.get("external_msg_id")

        instances.append(
            ParserRawMessage(
                source_id=source_id,
                external_msg_id=external_msg_id,
                raw_text=msg.get("raw_text"),
                metadata=msg.get("metadata", {}),
            )
        )

        latest_parsed_ids[source_id] = external_msg_id

    return ParseResult(
        instances=instances, latest_parsed_ids=MappingProxyType(latest_parsed_ids)
    )


def atomic_saved_messages_and_update_sources(messages_data: list) -> None:
    """
    Atomically uploads all dirty messages to the database and updates the id of the last message in the sources
    """

    parse_result = _create_object_list_and_search_last_ids(messages_data=messages_data)

    with transaction.atomic():
        ParserRawMessage.objects.bulk_create(
            parse_result.instances, batch_size=100, ignore_conflicts=True
        )
        sources_services.update_last_message_ids(
            new_last_ids=parse_result.latest_parsed_ids
        )
