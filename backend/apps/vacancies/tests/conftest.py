from datetime import date

import pytest
from django.db.models import QuerySet
from tests.factories import (
    INT_1_ID,
    INT_2_ID,
    INT_3_ID,
    INT_4_ID,
    INT_5_ID,
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    UUID_4_ID,
    UUID_5_ID,
    ContactFactory,
    LocationFactory,
    SkillFactory,
    SourceFactory,
    UserFactory,
    VacancyFactory,
    WorkFormatFactory,
)

from apps.vacancies.models import Vacancy


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
def setup_work_formats(db) -> None:
    WorkFormatFactory(id=INT_1_ID, name="Remote", slug="remote")
    WorkFormatFactory(id=INT_2_ID, name="Office", slug="office")
    WorkFormatFactory(id=INT_3_ID, name="Hybrid", slug="hybrid")


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
def setup_vacancies(
    db,
    setup_locations,
    setup_skills,
    setup_sources,
    setup_users,
    setup_contacts,
    setup_work_formats,
) -> None:
    loc_1 = LocationFactory._meta.model.objects.get(id=INT_1_ID)
    loc_2 = LocationFactory._meta.model.objects.get(id=INT_2_ID)
    loc_3 = LocationFactory._meta.model.objects.get(id=INT_3_ID)

    src_1 = SourceFactory._meta.model.objects.get(id=UUID_1_ID)
    src_2 = SourceFactory._meta.model.objects.get(id=UUID_2_ID)

    user_1 = UserFactory._meta.model.objects.get(id=UUID_1_ID)

    VacancyFactory(
        id=UUID_1_ID,
        source=src_1,
        author=None,
        location=loc_1,
        title="JavaScript Developer",
        description="Description 1",
        usd_salary_min=1700,
        status="ACT",
        grade="JUN",
        employment_type="FT",
        skills=[INT_1_ID, INT_3_ID, INT_4_ID],
        work_formats=[INT_1_ID, INT_3_ID],
        content_hash="hash_1",
        published_at=date(year=2026, month=5, day=24),
    )
    VacancyFactory(
        id=UUID_2_ID,
        source=None,
        author=user_1,
        location=loc_1,
        title="Vacancy 2",
        description="Description 2",
        usd_salary_min=1500,
        status="ACT",
        grade="MID",
        employment_type="PT",
        skills=[INT_2_ID, INT_5_ID],
        work_formats=[INT_3_ID],
        content_hash="hash_2",
        published_at=date(year=2026, month=5, day=20),
    )
    VacancyFactory(
        id=UUID_3_ID,
        source=src_1,
        author=None,
        location=loc_1,
        title="Vacancy 3",
        description="Description 3",
        usd_salary_min=2000,
        status="ACT",
        grade="SEN",
        employment_type="FT",
        skills=[INT_2_ID, INT_3_ID, INT_5_ID],
        work_formats=[INT_2_ID],
        content_hash="hash_3",
        published_at=date(year=2026, month=5, day=23),
    )
    VacancyFactory(
        id=UUID_4_ID,
        source=src_2,
        author=None,
        location=loc_2,
        title="Vacancy 4",
        description="Description 4",
        usd_salary_min=2500,
        status="ACT",
        grade="SEN",
        employment_type="FT",
        skills=[INT_1_ID, INT_3_ID, INT_4_ID],
        work_formats=[INT_1_ID, INT_2_ID, INT_3_ID],
        content_hash="hash_4",
        published_at=date(year=2026, month=5, day=23),
    )
    VacancyFactory(
        id=UUID_5_ID,
        source=src_2,
        author=None,
        location=loc_3,
        title="Vacancy 5",
        description="Description 5",
        usd_salary_min=1500,
        status="ACT",
        grade="MID",
        employment_type="FT",
        skills=[INT_1_ID, INT_2_ID, INT_3_ID, INT_4_ID],
        work_formats=[INT_1_ID, INT_2_ID],
        content_hash="hash_5",
        published_at=date(year=2026, month=5, day=21),
    )


@pytest.fixture
def vacancies(setup_vacancies) -> QuerySet["Vacancy"]:
    queryset = Vacancy.objects.all()
    return queryset
