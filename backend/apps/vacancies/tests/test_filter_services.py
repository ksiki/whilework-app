import uuid
from typing import Any, Iterable

import pytest
from django.db.models import Q, QuerySet
from tests.factories import (
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    UUID_4_ID,
    UUID_5_ID,
)

from apps.vacancies import filter_services
from apps.vacancies.exceptions import UnknownModeError, UnknownSortingError
from apps.vacancies.models import Vacancy


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

    for i, expectation_id in enumerate(expectation):
        assert expectation_id == queryset[i].id


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
