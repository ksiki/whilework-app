from typing import Any
from unittest.mock import patch

import pytest
from tests.factories import (
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    SourceFactory,
    SourceTopicFactory,
)

from apps.inbox.models import ParserRawMessage
from apps.inbox.services import (
    _create_object_list_and_search_last_ids,
    atomic_saved_messages_and_update_sources,
)


@pytest.fixture
def sample_messages_data() -> list[dict[str, Any]]:
    return [
        {
            "source_id": UUID_1_ID,
            "topic_id": UUID_3_ID,
            "external_msg_id": "msg_100",
            "raw_text": "Ищем Python Backend разработчика",
            "metadata": {"author": "HR"},
        },
        {
            "source_id": UUID_1_ID,
            "topic_id": UUID_3_ID,
            "external_msg_id": "msg_101",
            "raw_text": "Вакансия Data Engineer",
            "metadata": {},
        },
        {
            "source_id": UUID_2_ID,
            "topic_id": None,
            "external_msg_id": "post_55",
            "raw_text": "Middle Django Developer",
            "metadata": {"views": 150},
        },
    ]


@pytest.fixture
def setup_sources(db) -> None:
    source_1 = SourceFactory(id=UUID_1_ID, is_active=True)
    SourceTopicFactory(id=UUID_3_ID, source=source_1, is_active=True)

    SourceFactory(id=UUID_2_ID, is_active=True)


def test_create_object_list_and_search_last_ids(sample_messages_data) -> None:
    result = _create_object_list_and_search_last_ids(sample_messages_data)

    assert len(result.instances) == 3
    assert all(isinstance(obj, ParserRawMessage) for obj in result.instances)

    assert result.instances[0].source_id == UUID_1_ID
    assert result.instances[0].topic_id == UUID_3_ID
    assert result.instances[0].external_msg_id == "msg_100"
    assert result.instances[0].raw_text == "Ищем Python Backend разработчика"

    assert dict(result.latest_topic_ids) == {
        UUID_3_ID: "msg_101",
    }
    assert dict(result.latest_source_ids) == {
        UUID_2_ID: "post_55",
    }


@pytest.mark.django_db
@patch("apps.inbox.services.sources_services.update_last_parsed_message_ids")
def test_atomic_saved_messages_and_update_sources(
    mock_update_sources, sample_messages_data, setup_sources
) -> None:
    atomic_saved_messages_and_update_sources(sample_messages_data)

    assert ParserRawMessage.objects.count() == 3

    saved_msg = ParserRawMessage.objects.get(external_msg_id="msg_100")
    assert saved_msg.status == "PND"
    assert saved_msg.source_id == UUID_1_ID
    assert saved_msg.topic_id == UUID_3_ID

    atomic_saved_messages_and_update_sources(sample_messages_data)
    assert ParserRawMessage.objects.count() == 3

    assert mock_update_sources.called

    called_kwargs = mock_update_sources.call_args.kwargs
    assert "source_updates" in called_kwargs
    assert "topic_updates" in called_kwargs

    assert dict(called_kwargs["source_updates"]) == {
        UUID_2_ID: "post_55",
    }
    assert dict(called_kwargs["topic_updates"]) == {
        UUID_3_ID: "msg_101",
    }
