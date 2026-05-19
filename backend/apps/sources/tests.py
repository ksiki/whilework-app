import uuid
from types import MappingProxyType

import pytest

from .models import Source
from .services import (
    get_active_sources,
    register_source_error,
    update_last_parsed_message_ids,
)

SOURCE_1_ID = uuid.UUID("11111111-1111-4111-a111-111111111111")
SOURCE_2_ID = uuid.UUID("22222222-2222-4222-a222-222222222222")
SOURCE_3_ID = uuid.UUID("33333333-3333-4333-a333-333333333333")
NOT_EXISTS_ID = uuid.UUID("44444444-4444-4444-a444-444444444444")


@pytest.fixture
def setup_sources(db) -> None:
    Source.objects.create(
        id=SOURCE_1_ID,
        name="Telegram Python Jobs",
        platform="telegram",
        identifier="tg_python_jobs",
        error_count=3,
        is_active=True,
    )
    Source.objects.create(
        id=SOURCE_2_ID,
        name="Discord Data Eng",
        platform="discord",
        identifier="discord_data_eng",
        is_active=False,
    )
    Source.objects.create(
        id=SOURCE_3_ID,
        name="Discord Data Jobs",
        platform="discord",
        identifier="discord_data_jobs",
        is_active=True,
    )


@pytest.mark.django_db
def test_get_active_sources(setup_sources) -> None:
    result = get_active_sources()

    assert len(result) == 2
    assert result[0].id == SOURCE_1_ID
    assert result[1].id == SOURCE_3_ID


@pytest.mark.django_db
def test_update_last_message_ids(setup_sources) -> None:
    source = Source.objects.get(id=SOURCE_1_ID)

    assert source.last_parsed_id is None

    data = MappingProxyType({SOURCE_1_ID: "999"})
    update_last_parsed_message_ids(new_last_ids=data)
    updated_source = Source.objects.get(id=SOURCE_1_ID)

    assert updated_source.last_parsed_id == "999"


@pytest.mark.django_db
def test_register_source_error(setup_sources) -> None:
    source = Source.objects.get(id=SOURCE_1_ID)

    assert source.error_count == 3
    assert source.last_error_message is None

    register_source_error(source_id=SOURCE_1_ID, error_message="Error_1")
    source = Source.objects.get(id=SOURCE_1_ID)

    assert source.error_count == 4
    assert source.last_error_message == "Error_1"
    assert source.is_active is True

    register_source_error(source_id=SOURCE_1_ID, error_message="Error_2")
    source = Source.objects.get(id=SOURCE_1_ID)

    assert source.error_count == 5
    assert source.last_error_message == "Error_2"
    assert source.is_active is False

    with pytest.raises(Source.DoesNotExist):
        assert register_source_error(source_id=NOT_EXISTS_ID, error_message="Error_3")
