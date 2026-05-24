import pytest
from apps.sources.models import Source
from tests.factories import SOURCE_1_ID, SOURCE_2_ID, SOURCE_3_ID


@pytest.fixture
def setup_sources(db) -> None:
    Source.objects.create(
        id=SOURCE_1_ID,
        name="Telegram Python Jobs",
        platform="TLG",
        identifier="tg_python_jobs",
        error_count=3,
        is_active=True,
    )
    Source.objects.create(
        id=SOURCE_2_ID,
        name="Discord Data Eng",
        platform="DIS",
        identifier="discord_data_eng",
        is_active=False,
    )
    Source.objects.create(
        id=SOURCE_3_ID,
        name="Discord Data Jobs",
        platform="DIS",
        identifier="discord_data_jobs",
        is_active=True,
    )
