import uuid
from types import MappingProxyType
from typing import Final

import pytest
from tests.factories import UUID_1_ID, UUID_2_ID, SourceFactory

from .models import Source
from .services import (
    get_active_sources,
    register_source_error,
    update_last_parsed_message_ids,
)

NOT_EXISTS_ID: Final[uuid.UUID] = uuid.UUID("44444444-4444-4444-a444-444444444444")


@pytest.fixture
def setup_sources(db) -> None:
    SourceFactory(id=UUID_1_ID, error_count=3, is_active=True)
    SourceFactory(is_active=False)
    SourceFactory(id=UUID_2_ID, is_active=True)


@pytest.mark.django_db
def test_get_active_sources(setup_sources) -> None:
    result = get_active_sources()

    assert len(result) == 2
    assert result[0].id == UUID_1_ID
    assert result[1].id == UUID_2_ID


@pytest.mark.django_db
def test_update_last_message_ids(setup_sources) -> None:
    source = Source.objects.get(id=UUID_1_ID)
    assert source.last_parsed_id is None

    data = MappingProxyType({UUID_1_ID: "999"})
    update_last_parsed_message_ids(new_last_ids=data)

    source.refresh_from_db()
    assert source.last_parsed_id == "999"


@pytest.mark.django_db
def test_register_source_error(setup_sources) -> None:
    source = Source.objects.get(id=UUID_1_ID)

    assert source.error_count == 3
    assert source.last_error_message is None

    register_source_error(source_id=UUID_1_ID, error_message="Error_1")
    source = Source.objects.get(id=UUID_1_ID)

    assert source.error_count == 4
    assert source.last_error_message == "Error_1"
    assert source.is_active is True

    register_source_error(source_id=UUID_1_ID, error_message="Error_2")
    source = Source.objects.get(id=UUID_1_ID)

    assert source.error_count == 5
    assert source.last_error_message == "Error_2"
    assert source.is_active is False

    with pytest.raises(Source.DoesNotExist):
        register_source_error(source_id=NOT_EXISTS_ID, error_message="Error_3")
