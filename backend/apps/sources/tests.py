import uuid
from types import MappingProxyType
from typing import Final

import pytest
from tests.factories import (
    UUID_1_ID,
    UUID_2_ID,
    UUID_4_ID,
    UUID_5_ID,
    SourceFactory,
    SourceTopicFactory,
)

from .models import Source, SourceTopic
from .services import (
    get_active_sources,
    register_parsing_error,
    update_last_parsed_message_ids,
)

NOT_EXISTS_ID: Final[uuid.UUID] = uuid.UUID("44444444-4444-4444-a444-444444444444")


@pytest.fixture
def setup_sources(db) -> None:
    source_1 = SourceFactory(id=UUID_1_ID, error_count=3, is_active=True)
    SourceTopicFactory(id=UUID_4_ID, source=source_1, is_active=True, error_count=3)
    SourceTopicFactory(id=UUID_5_ID, source=source_1, is_active=False)

    SourceFactory(is_active=False)

    SourceFactory(id=UUID_2_ID, is_active=True)


@pytest.mark.django_db
def test_get_active_sources(setup_sources) -> None:
    result = get_active_sources()

    assert len(result) == 2

    source_1 = next(s for s in result if s.id == UUID_1_ID)
    source_2 = next(s for s in result if s.id == UUID_2_ID)

    assert hasattr(source_1, "active_topics")
    assert len(source_1.active_topics) == 1
    assert source_1.active_topics[0].id == UUID_4_ID

    assert hasattr(source_2, "active_topics")
    assert len(source_2.active_topics) == 0


@pytest.mark.django_db
def test_update_last_message_ids(setup_sources) -> None:
    source = Source.objects.get(id=UUID_1_ID)
    topic = SourceTopic.objects.get(id=UUID_4_ID)

    assert source.last_parsed_id is None
    assert topic.last_parsed_id is None

    source_updates = MappingProxyType({UUID_1_ID: "999"})
    topic_updates = MappingProxyType({UUID_4_ID: "888"})

    update_last_parsed_message_ids(
        source_updates=source_updates, topic_updates=topic_updates
    )

    source.refresh_from_db()
    topic.refresh_from_db()

    assert source.last_parsed_id == "999"
    assert topic.last_parsed_id == "888"


@pytest.mark.django_db
def test_register_parsing_error_for_source(setup_sources) -> None:
    source = Source.objects.get(id=UUID_1_ID)

    assert source.error_count == 3
    assert source.last_error_message is None

    register_parsing_error(target_id=UUID_1_ID, error_message="Error_1", is_topic=False)
    source.refresh_from_db()

    assert source.error_count == 4
    assert source.last_error_message == "Error_1"
    assert source.is_active is True

    register_parsing_error(target_id=UUID_1_ID, error_message="Error_2", is_topic=False)
    source.refresh_from_db()

    assert source.error_count == 5
    assert source.last_error_message == "Error_2"
    assert source.is_active is False

    with pytest.raises(Source.DoesNotExist):
        register_parsing_error(
            target_id=NOT_EXISTS_ID, error_message="Error_3", is_topic=False
        )


@pytest.mark.django_db
def test_register_parsing_error_for_topic(setup_sources) -> None:
    topic = SourceTopic.objects.get(id=UUID_4_ID)
    source = Source.objects.get(id=UUID_1_ID)

    assert topic.error_count == 3
    assert topic.last_error_message is None

    register_parsing_error(
        target_id=UUID_4_ID, error_message="Topic_Error_1", is_topic=True
    )
    topic.refresh_from_db()

    assert topic.error_count == 4
    assert topic.last_error_message == "Topic_Error_1"
    assert topic.is_active is True

    register_parsing_error(
        target_id=UUID_4_ID, error_message="Topic_Error_2", is_topic=True
    )
    topic.refresh_from_db()
    source.refresh_from_db()

    assert topic.error_count == 5
    assert topic.last_error_message == "Topic_Error_2"
    assert topic.is_active is False

    assert source.is_active is True

    with pytest.raises(SourceTopic.DoesNotExist):
        register_parsing_error(
            target_id=NOT_EXISTS_ID, error_message="Error_3", is_topic=True
        )
