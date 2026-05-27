import pytest
from tests.factories import (
    INT_1_ID,
    INT_2_ID,
    INT_3_ID,
    INT_4_ID,
    INT_5_ID,
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    ContactFactory,
    LocationFactory,
    SkillFactory,
    SourceFactory,
    UserFactory,
)


@pytest.fixture
def setup_locations(db) -> None:
    LocationFactory(
        id=INT_1_ID, region="Europe", country="Czech Republic", city="Prague"
    )
    LocationFactory(id=INT_2_ID, region="CIS(СНГ)", country="Belarus", city="Minsk")
    LocationFactory(id=INT_3_ID, region="CIS(СНГ)", country="Russia", city="Moskow")


@pytest.fixture
def setup_skills(db) -> None:
    SkillFactory(id=INT_1_ID, name="Python", slug="python")
    SkillFactory(id=INT_2_ID, name="JavaScript", slug="javascript")
    SkillFactory(id=INT_3_ID, name="SQL", slug="sql")
    SkillFactory(id=INT_4_ID, name="Airflow", slug="airflow")
    SkillFactory(id=INT_5_ID, name="Redis", slug="redis")


@pytest.fixture
def setup_contacts(db) -> None:
    ContactFactory(id=UUID_1_ID, platform="TG")
    ContactFactory(id=UUID_2_ID, platform="TG")
    ContactFactory(id=UUID_3_ID, platform="EM")


@pytest.fixture
def setup_sources(db) -> None:
    SourceFactory(id=UUID_1_ID, platform="TLG", is_active=True)
    SourceFactory(id=UUID_2_ID, platform="DIS", is_active=True)


@pytest.fixture
def setup_users(db) -> None:
    UserFactory(id=UUID_1_ID)


@pytest.fixture
def create_environments(
    setup_locations,
    setup_skills,
    setup_sources,
    setup_users,
    setup_contacts,
) -> None:
    pass
