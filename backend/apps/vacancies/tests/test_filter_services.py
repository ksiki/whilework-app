import uuid
from datetime import date
from typing import Any, Iterable

import pytest
from django.db.models import Q, QuerySet
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
    LocationFactory,
    SourceFactory,
    UserFactory,
    VacancyFactory,
)

from apps.vacancies import filter_services
from apps.vacancies.exceptions import UnknownModeError, UnknownSortingError
from apps.vacancies.models import Vacancy


@pytest.fixture
def setup_vacancies(db, create_environments) -> None:
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
        status=Vacancy.Status.ACTIVE,
        grade=Vacancy.Grade.JUNIOR,
        experience_from=None,
        employment_type=Vacancy.EmploymentType.FULL_TIME,
        skills=[INT_1_ID, INT_3_ID, INT_4_ID],
        work_format=Vacancy.WorkFormat.REMOTE,
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
        status=Vacancy.Status.ACTIVE,
        grade=Vacancy.Grade.MIDDLE,
        experience_from=1,
        employment_type=Vacancy.EmploymentType.PART_TIME,
        skills=[INT_2_ID, INT_5_ID],
        work_format=Vacancy.WorkFormat.REMOTE,
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
        status=Vacancy.Status.ACTIVE,
        grade=Vacancy.Grade.SENIOR,
        experience_from=3,
        employment_type=Vacancy.EmploymentType.FULL_TIME,
        skills=[INT_2_ID, INT_3_ID, INT_5_ID],
        work_format=Vacancy.WorkFormat.OFFICE,
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
        status=Vacancy.Status.ACTIVE,
        grade=Vacancy.Grade.SENIOR,
        experience_from=4,
        employment_type=Vacancy.EmploymentType.FULL_TIME,
        skills=[INT_1_ID, INT_3_ID, INT_4_ID],
        work_format=Vacancy.WorkFormat.HYBRID,
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
        status=Vacancy.Status.ACTIVE,
        grade=Vacancy.Grade.MIDDLE,
        experience_from=0,
        employment_type=Vacancy.EmploymentType.FULL_TIME,
        skills=[INT_1_ID, INT_2_ID, INT_3_ID, INT_4_ID],
        work_format=Vacancy.WorkFormat.HYBRID,
        content_hash="hash_5",
        published_at=date(year=2026, month=5, day=21),
    )


@pytest.fixture
def vacancies(setup_vacancies) -> QuerySet["Vacancy"]:
    queryset = Vacancy.objects.all()
    return queryset


def assert_queryset_match_expectation(
    queryset: QuerySet["Vacancy"], expectation: Iterable[uuid.UUID]
) -> None:
    assert len(queryset) == len(expectation)
    assert all(vacancy.id in expectation for vacancy in queryset)


@pytest.mark.parametrize(
    "mode, data_for_q, expectation",
    [
        ("choose", (UUID_1_ID, UUID_2_ID), (UUID_1_ID, UUID_2_ID)),
        ("exclude", (UUID_1_ID, UUID_2_ID), (UUID_3_ID, UUID_4_ID, UUID_5_ID)),
    ],
)
@pytest.mark.django_db
def test_apply_q_object(
    mode: str | None,
    data_for_q: tuple[uuid.UUID],
    expectation: tuple[uuid.UUID],
    vacancies: QuerySet["Vacancy"],
) -> None:
    q = Q(id__in=data_for_q)
    queryset = filter_services._apply_q_object(queryset=vacancies, q_obj=q, mode=mode)

    assert_queryset_match_expectation(queryset=queryset, expectation=expectation)


@pytest.mark.parametrize(
    "sort_by, expectation",
    [
        ("date", (UUID_1_ID, UUID_4_ID, UUID_3_ID, UUID_5_ID, UUID_2_ID)),
        ("salary", (UUID_4_ID, UUID_3_ID, UUID_1_ID, UUID_5_ID, UUID_2_ID)),
    ],
)
@pytest.mark.django_db
def test_apply_sorting(
    sort_by: str, expectation: tuple[uuid.UUID], vacancies: QuerySet["Vacancy"]
) -> None:
    queryset = filter_services.apply_sorting(queryset=vacancies, sort_by=sort_by)

    assert len(expectation) == len(queryset)
    for expectation_id, sorting_vacancy in zip(expectation, queryset):
        assert expectation_id == sorting_vacancy.id


@pytest.mark.parametrize(
    "search_data, expectation",
    [
        (
            {
                "query": "2",
                "fields": ["title"],
            },
            (UUID_2_ID,),
        ),
        (
            {
                "query": "sql",
                "fields": ["skills"],
            },
            (UUID_1_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "query": "javascript",
                "fields": ["title", "skills"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_5_ID),
        ),
    ],
)
@pytest.mark.django_db
def test_apply_text_search(
    search_data: dict[str, Any],
    expectation: tuple[uuid.UUID],
    vacancies: QuerySet["Vacancy"],
) -> None:
    queryset = filter_services.apply_text_search(
        queryset=vacancies, search_data=search_data
    )

    assert_queryset_match_expectation(queryset=queryset, expectation=expectation)


@pytest.mark.parametrize(
    "geo_data, expectation",
    [
        (
            {
                "mode": "choose",
                "category": "regions",
                "items": [],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "mode": "choose",
                "category": "reg",
                "items": ["Europe"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "mode": "choose",
                "category": "regions",
                "items": ["Europe"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID),
        ),
        (
            {
                "mode": "choose",
                "category": "countries",
                "items": ["Belarus", "Russia"],
            },
            (UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "mode": "choose",
                "category": "cities",
                "items": ["Moskow"],
            },
            (UUID_5_ID,),
        ),
        (
            {
                "mode": "exclude",
                "category": "regions",
                "items": ["Europe"],
            },
            (UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "mode": "exclude",
                "category": "countries",
                "items": ["Belarus", "Russia"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID),
        ),
        (
            {
                "mode": "exclude",
                "category": "cities",
                "items": ["Moskow"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID),
        ),
    ],
)
@pytest.mark.django_db
def test_apply_geo_filters(
    geo_data: dict[str, Any],
    expectation: tuple[uuid.UUID],
    vacancies: QuerySet["Vacancy"],
) -> None:
    queryset = filter_services.apply_geo_filters(queryset=vacancies, geo_data=geo_data)

    assert_queryset_match_expectation(queryset=queryset, expectation=expectation)


@pytest.mark.parametrize(
    "sources_data, expectation",
    [
        (
            {
                "mode": "choose",
                "items": [],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "mode": "choose",
                "items": ["TLG", "DIS"],
            },
            (UUID_1_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            {
                "mode": "choose",
                "items": ["TLG", "WhileWork"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID),
        ),
        (
            {
                "mode": "exclude",
                "items": ["TLG"],
            },
            (UUID_2_ID, UUID_4_ID, UUID_5_ID),
        ),
    ],
)
@pytest.mark.django_db
def test_apply_source_filters(
    sources_data: dict[str, Any],
    expectation: tuple[uuid.UUID],
    vacancies: QuerySet["Vacancy"],
) -> None:
    queryset = filter_services.apply_source_filters(
        queryset=vacancies, sources_data=sources_data
    )

    assert_queryset_match_expectation(queryset=queryset, expectation=expectation)


@pytest.mark.parametrize(
    "experience, expectation",
    [
        (
            0,
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            3,
            (UUID_3_ID, UUID_4_ID),
        ),
        (
            None,
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
    ],
)
@pytest.mark.django_db
def test_apply_experience_filters(
    experience: int,
    expectation: tuple[uuid.UUID],
    vacancies: QuerySet["Vacancy"],
) -> None:
    queryset = filter_services.apply_experience_filters(
        queryset=vacancies, experience_from=experience
    )

    assert_queryset_match_expectation(queryset=queryset, expectation=expectation)


@pytest.mark.parametrize(
    "db_field, filter_data, expectation",
    [
        (
            "skills__slug",
            {
                "mode": "choose",
                "logic": "and",
                "items": [],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
        (
            "skills__slug",
            {
                "mode": "choose",
                "logic": "and",
                "items": ["sql", "javascript"],
            },
            (UUID_3_ID, UUID_5_ID),
        ),
        (
            "skills__slug",
            {
                "mode": "choose",
                "logic": "or",
                "items": ["sql", "javascript"],
            },
            (UUID_1_ID, UUID_2_ID, UUID_3_ID, UUID_4_ID, UUID_5_ID),
        ),
    ],
)
@pytest.mark.django_db
def test_apply_dynamic_filter(
    db_field: str,
    filter_data: dict[str, Any],
    expectation: tuple[uuid.UUID],
    vacancies: QuerySet["Vacancy"],
) -> None:
    queryset = filter_services.apply_dynamic_filter(
        queryset=vacancies, db_field=db_field, filter_data=filter_data
    )

    assert_queryset_match_expectation(queryset=queryset, expectation=expectation)


def test_apply_q_object_uncnown_mode(vacancies) -> None:
    with pytest.raises(UnknownModeError):
        filter_services._apply_q_object(queryset=vacancies, q_obj=Q(), mode="uncnown")


def test_apply_sorting_uncnown_sorting(vacancies) -> None:
    with pytest.raises(UnknownSortingError):
        filter_services.apply_sorting(queryset=vacancies, sort_by="uncnown")
