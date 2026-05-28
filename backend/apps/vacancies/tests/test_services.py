from datetime import date
from unittest.mock import MagicMock

import pytest
from django.db.models import QuerySet
from tests.factories import (
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    UUID_4_ID,
    UUID_5_ID,
    UUID_6_ID,
    VacancyFactory,
)

from apps.vacancies import services
from apps.vacancies.models import Vacancy


@pytest.fixture
def mock_filter_services(mocker):
    base_path = "apps.vacancies.filter_services"

    return {
        "text": mocker.patch(
            f"{base_path}.apply_text_search", side_effect=lambda qs, *args: qs
        ),
        "geo": mocker.patch(
            f"{base_path}.apply_geo_filters", side_effect=lambda qs, *args: qs
        ),
        "source": mocker.patch(
            f"{base_path}.apply_source_filters", side_effect=lambda qs, *args: qs
        ),
        "experience": mocker.patch(
            f"{base_path}.apply_experience_filters", side_effect=lambda qs, *args: qs
        ),
        "dynamic": mocker.patch(
            f"{base_path}.apply_dynamic_filter", side_effect=lambda qs, *args: qs
        ),
        "sorting": mocker.patch(
            f"{base_path}.apply_sorting", side_effect=lambda qs, *args: qs
        ),
    }


@pytest.fixture
def setup_vacancies(db, create_environments) -> None:
    VacancyFactory(
        id=UUID_1_ID,
        location=None,
        published_at=date(year=2026, month=5, day=25),
        content_hash="1",
        status=Vacancy.Status.ACTIVE,
    )
    VacancyFactory(
        id=UUID_2_ID,
        location=None,
        published_at=date(year=2026, month=5, day=25),
        content_hash="2",
        status=Vacancy.Status.ARCHIVED,
    )
    VacancyFactory(
        id=UUID_3_ID,
        location=None,
        published_at=date(year=2026, month=5, day=20),
        content_hash="3",
        status=Vacancy.Status.CLOSED,
    )
    VacancyFactory(
        id=UUID_4_ID,
        location=None,
        published_at=date(year=2026, month=3, day=15),
        content_hash="4",
        status=Vacancy.Status.ACTIVE,
    )
    VacancyFactory(
        id=UUID_5_ID,
        location=None,
        published_at=date(year=2026, month=5, day=5),
        content_hash="5",
        status=Vacancy.Status.ACTIVE,
    )
    VacancyFactory(
        id=UUID_6_ID,
        location=None,
        published_at=date(year=2026, month=5, day=5),
        content_hash="6",
        status=Vacancy.Status.ACTIVE,
    )


@pytest.fixture
def vacancies(setup_vacancies) -> QuerySet["Vacancy"]:
    queryset = Vacancy.objects.all()
    return queryset


@pytest.mark.django_db
def test_get_active_vacancies(setup_vacancies) -> None:
    queryset = services.get_active_vacancies()

    assert len(queryset) == 3

    expectation = (UUID_1_ID, UUID_5_ID, UUID_6_ID)
    assert all(vacancy.id in expectation for vacancy in queryset)


@pytest.mark.django_db
def test_get_page(vacancies: QuerySet["Vacancy"]) -> None:
    page = services.get_page(queryset=vacancies, page_number=1)

    vacancies_from_page = page.object_list
    assert len(vacancies_from_page) == 6
    assert page.has_next() is False


@pytest.mark.django_db
def test_apply_filters_orchestration(mock_filter_services, mocker):
    mock_qs = MagicMock()
    params = {
        "search": {"query": "python"},
        "geo": {"city": "Prague"},
        "sources": {"platform": "TG"},
        "experience_from": "3",
        "sort": "salary",
        list(services.FILTER_MAPPING.keys())[0]: {"some": "data"},
    }
    dynamic_key = list(services.FILTER_MAPPING.keys())[0]
    dynamic_field = services.FILTER_MAPPING[dynamic_key]

    result = services.apply_filters(queryset=mock_qs, params=params)

    mock_filter_services["text"].assert_called_once_with(mock_qs, params["search"])
    mock_filter_services["geo"].assert_called_once_with(mock_qs, params["geo"])
    mock_filter_services["source"].assert_called_once_with(mock_qs, params["sources"])

    mock_filter_services["experience"].assert_called_once_with(mock_qs, 3)

    mock_filter_services["dynamic"].assert_called_once_with(
        mock_qs, dynamic_field, params[dynamic_key]
    )
    mock_filter_services["sorting"].assert_called_once_with(mock_qs, "salary")

    mock_qs.prefetch_related.assert_called_once_with("skills")

    assert result == mock_qs.prefetch_related.return_value


@pytest.mark.django_db
def test_apply_filters_empty_experience(mock_filter_services):
    mock_qs = MagicMock()
    params = {
        "experience_from": "",
    }

    services.apply_filters(queryset=mock_qs, params=params)

    mock_filter_services["experience"].assert_called_once_with(mock_qs, 0)
