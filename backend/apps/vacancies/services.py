import logging
from datetime import timedelta
from types import MappingProxyType
from typing import Any, Final

from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.utils import timezone

from apps.sources import services as sources_services

from . import filter_services
from .models import Location, Skill, Vacancy

logger = logging.getLogger(__name__)


def get_active_vacancies() -> QuerySet["Vacancy"]:
    """
    Returns the list of active vacancies for the last 30 days
    """

    period = timezone.now() - timedelta(days=30)
    return Vacancy.objects.filter(
        published_at__gt=period,
        status=Vacancy.Status.ACTIVE,
    )


def get_page(
    queryset: QuerySet["Vacancy"], page_number: int, per_page: int = 10
) -> Page:
    paginator = Paginator(object_list=queryset, per_page=per_page)
    return paginator.get_page(number=page_number)


FILTER_MAPPING: Final[MappingProxyType] = MappingProxyType(
    {
        "grade": "grade",
        "work_format": "work_format",
        "work_type": "employment_type",
        "skills": "skills__slug",
    }
)


def apply_filters(
    queryset: QuerySet["Vacancy"], params: dict[str, Any]
) -> QuerySet["Vacancy"]:
    search_data = params.get("search", {})
    queryset = filter_services.apply_text_search(queryset, search_data)

    geo_data = params.get("geo", {})
    queryset = filter_services.apply_geo_filters(queryset, geo_data)

    sources_data = params.get("sources", {})
    queryset = filter_services.apply_source_filters(queryset, sources_data)

    raw_experience = params.get("experience_from")
    experience_from = int(raw_experience) if raw_experience else 0
    queryset = filter_services.apply_experience_filters(queryset, experience_from)

    for filter_key, db_field in FILTER_MAPPING.items():
        filter_data = params.get(filter_key, {})
        if filter_data:
            queryset = filter_services.apply_dynamic_filter(
                queryset, db_field, filter_data
            )

    sort_by = params.get("sort", "date")
    queryset = filter_services.apply_sorting(queryset, sort_by)

    return queryset.prefetch_related("skills")


def make_context_for_vacancies_list() -> dict[str, Any]:
    skills = list(Skill.objects.values("slug", "name"))

    regions = list(
        Location.objects.exclude(region="").values_list("region", flat=True).distinct()
    )
    countries = list(
        Location.objects.exclude(country="")
        .values_list("country", flat=True)
        .distinct()
    )
    cities = list(
        Location.objects.exclude(city="").values_list("city", flat=True).distinct()
    )

    return {
        "sources": sources_services.get_source_types(),
        "work_formats": Vacancy.WorkFormat.choices,
        "grades": Vacancy.Grade.choices,
        "employment_types": Vacancy.EmploymentType.choices,
        "skills": skills,
        "geo": {
            "regions": regions,
            "countries": countries,
            "cities": cities,
        },
    }
