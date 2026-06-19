import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import QuerySet
from django.utils import timezone
from tests.factories import (
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    UUID_4_ID,
    UUID_5_ID,
    UUID_6_ID,
    UserFactory,
    VacancyFactory,
)

from apps.vacancies import services
from apps.vacancies.models import Vacancy


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture
def mock_filter_services(mocker):
    base_path = "apps.vacancies.filter_services"

    return {
        "blacklist": mocker.patch(
            f"{base_path}.apply_blacklist_companies", side_effect=lambda qs, *args: qs
        ),
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
        "salary": mocker.patch(
            f"{base_path}.apply_salary_filters", side_effect=lambda qs, *args: qs
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
    now = timezone.now()

    VacancyFactory(
        id=UUID_1_ID,
        location=None,
        published_at=now,
        content_hash="1",
        status=Vacancy.Status.ACTIVE,
    )
    VacancyFactory(
        id=UUID_2_ID,
        location=None,
        published_at=now,
        content_hash="2",
        status=Vacancy.Status.ARCHIVED,
    )
    VacancyFactory(
        id=UUID_3_ID,
        location=None,
        published_at=now - timedelta(days=5),
        content_hash="3",
        status=Vacancy.Status.CLOSED,
    )
    VacancyFactory(
        id=UUID_4_ID,
        location=None,
        published_at=now - timedelta(days=70),
        content_hash="4",
        status=Vacancy.Status.ACTIVE,
    )
    VacancyFactory(
        id=UUID_5_ID,
        location=None,
        published_at=now - timedelta(days=20),
        content_hash="5",
        status=Vacancy.Status.ACTIVE,
    )
    VacancyFactory(
        id=UUID_6_ID,
        location=None,
        published_at=now - timedelta(days=20),
        content_hash="6",
        status=Vacancy.Status.ACTIVE,
    )


@pytest.fixture
def vacancies(setup_vacancies) -> QuerySet["Vacancy"]:
    queryset = Vacancy.objects.all()
    return queryset


@pytest.mark.django_db
def test_get_active_vacancies_logic(setup_vacancies):
    queryset = services.get_active_vacancies()

    assert len(queryset) == 3
    expectation = {UUID_1_ID, UUID_5_ID, UUID_6_ID}
    assert {v.id for v in queryset} == expectation


@pytest.mark.django_db
def test_cache_is_populated(setup_vacancies):
    services.get_active_vacancies()

    cached_ids = cache.get("active_vacancy_ids")
    assert cached_ids is not None
    assert len(cached_ids) == 3


@pytest.mark.django_db
def test_get_page(vacancies: QuerySet["Vacancy"]) -> None:
    page = services.get_page(queryset=vacancies, page_number=1)

    vacancies_from_page = page.object_list
    assert len(vacancies_from_page) == 6
    assert page.has_next() is False


@pytest.mark.django_db
def test_apply_filters_orchestration(mock_filter_services, mocker):
    mock_qs = MagicMock()
    mock_blacklist = [uuid.uuid4()]

    params = {
        "search": {"query": "python"},
        "geo": {"city": "Prague"},
        "sources": {"platform": "TG"},
        "experience_from": "3",
        "salary_min": "10000",
        "sort": "salary",
        list(services.FILTER_MAPPING.keys())[0]: {"some": "data"},
    }
    dynamic_key = list(services.FILTER_MAPPING.keys())[0]
    dynamic_field = services.FILTER_MAPPING[dynamic_key]

    result = services.apply_filters(
        queryset=mock_qs, blacklist_companies=mock_blacklist, params=params
    )

    mock_filter_services["blacklist"].assert_called_once_with(mock_qs, mock_blacklist)
    mock_filter_services["text"].assert_called_once_with(mock_qs, params["search"])
    mock_filter_services["geo"].assert_called_once_with(mock_qs, params["geo"])
    mock_filter_services["source"].assert_called_once_with(mock_qs, params["sources"])
    mock_filter_services["experience"].assert_called_once_with(mock_qs, 3)
    mock_filter_services["salary"].assert_called_once_with(mock_qs, 10000)
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

    services.apply_filters(queryset=mock_qs, blacklist_companies=None, params=params)

    mock_filter_services["blacklist"].assert_called_once_with(mock_qs, None)
    mock_filter_services["experience"].assert_called_once_with(mock_qs, 0)


@pytest.mark.django_db
def test_vacancies_by_owner():
    user = UserFactory()
    v1 = VacancyFactory(author=user, content_hash=str(uuid.uuid4()))
    v2 = VacancyFactory(author=user, content_hash=str(uuid.uuid4()))
    VacancyFactory(content_hash=str(uuid.uuid4()))

    qs = services.vacancies_by_owner(user.id)

    assert qs.count() == 2
    assert v1 in qs
    assert v2 in qs


@pytest.mark.asyncio
@patch("apps.vacancies.services.Complaint.objects.acreate", new_callable=AsyncMock)
async def test_add_complaint_success(mock_acreate):
    user_id = uuid.uuid4()
    payload = MagicMock(vacancy=uuid.uuid4(), reason="Spam", details="Text")

    result = await services.add_complaint(user_id, payload)

    assert result is True
    mock_acreate.assert_awaited_once_with(
        vacancy_id=payload.vacancy,
        author_id=user_id,
        reason=payload.reason,
        details=payload.details,
    )


@pytest.mark.asyncio
@patch("apps.vacancies.services.Complaint.objects.acreate", new_callable=AsyncMock)
async def test_add_complaint_integrity_error(mock_acreate):
    mock_acreate.side_effect = IntegrityError()
    payload = MagicMock()

    result = await services.add_complaint(uuid.uuid4(), payload)

    assert result is False


@patch("apps.vacancies.services.cache.get")
def test_get_similar_vacancies_cache_hit(mock_cache_get):
    v_id = uuid.uuid4()
    cached_ids = [uuid.uuid4(), uuid.uuid4()]
    mock_cache_get.return_value = cached_ids

    with patch("apps.vacancies.services.Vacancy.objects.filter") as mock_filter:
        services.get_similar_vacancies(v_id)
        mock_filter.assert_called_once()


@patch("apps.vacancies.services.cache.get")
def test_get_similar_vacancies_empty_cache_hit(mock_cache_get):
    mock_cache_get.return_value = []
    qs = services.get_similar_vacancies(uuid.uuid4())
    assert qs.count() == 0


@pytest.mark.django_db
def test_get_similar_vacancies_not_found():
    qs = services.get_similar_vacancies(uuid.uuid4())
    assert qs.count() == 0


@patch("apps.vacancies.services.Skill.objects.values")
@patch("apps.vacancies.services.Location.objects.exclude")
@patch("apps.vacancies.services.get_active_vacancies")
def test_make_context_for_vacancies_list(
    mock_get_active, mock_loc_exclude, mock_skills
):
    mock_skills.return_value = [{"slug": "py", "name": "Python"}]

    mock_qs = MagicMock()
    mock_qs.count.return_value = 100
    mock_qs.filter.return_value.count.return_value = 5
    mock_get_active.return_value = mock_qs

    mock_exclude_qs = MagicMock()
    mock_exclude_qs.values_list.return_value.distinct.return_value = ["Test"]
    mock_loc_exclude.return_value = mock_exclude_qs

    context = services.make_context_for_vacancies_list()

    assert context["skills"] == [{"slug": "py", "name": "Python"}]
    assert context["vacancies_per_month"] == 100
    assert context["vacancies_today"] == 5
    assert "work_formats" in context
    assert "grades" in context
    assert "geo" in context


@pytest.mark.django_db
def test_update_views():
    vacancy = VacancyFactory(views_count=0)

    services.update_views(vacancy, 2)
    assert vacancy.views_count == 2

    services.update_views(vacancy)
    assert vacancy.views_count == 3


@pytest.mark.asyncio
@patch("apps.vacancies.services.Vacancy.objects.filter")
async def test_update_contacts_views_success(mock_filter):
    mock_update = AsyncMock(return_value=1)
    mock_filter.return_value.aupdate = mock_update

    result = await services.update_contacts_views(uuid.uuid4())

    assert result is True
    mock_update.assert_awaited_once()


@pytest.mark.asyncio
@patch("apps.vacancies.services.Vacancy.objects.filter")
async def test_update_contacts_views_exception(mock_filter):
    mock_filter.return_value.aupdate = AsyncMock(side_effect=Exception("DB Error"))

    result = await services.update_contacts_views(uuid.uuid4())

    assert result is False
