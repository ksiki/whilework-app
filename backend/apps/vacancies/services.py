import logging
import uuid
from datetime import timedelta
from types import MappingProxyType
from typing import Any, Final

from django.contrib.postgres.search import TrigramSimilarity
from django.core.cache import cache
from django.core.paginator import Page, Paginator
from django.db import IntegrityError
from django.db.models import Case, Count, Q, QuerySet, When
from django.utils import timezone

from apps.vacancies.api.schemas import ComplaintRequest

from . import filter_services
from .models import Complaint, Location, Skill, Vacancy

logger = logging.getLogger(__name__)


def get_active_vacancies() -> QuerySet["Vacancy"]:
    cache_key = "active_vacancy_ids"
    vacancy_ids = cache.get(cache_key)

    if vacancy_ids is None:
        period = timezone.now() - timedelta(days=30)
        vacancy_ids = list(
            Vacancy.objects.filter(
                published_at__gt=period,
                status=Vacancy.Status.ACTIVE,
            ).values_list("id", flat=True)
        )

        cache.set(cache_key, vacancy_ids, timeout=1800)
    return Vacancy.objects.filter(id__in=vacancy_ids)


def vacancies_by_owner(owner_id: uuid.UUID) -> QuerySet["Vacancy"]:
    return Vacancy.objects.filter(author=owner_id)


def get_page(
    queryset: QuerySet["Vacancy"], page_number: int, per_page: int = 10
) -> Page:
    paginator = Paginator(object_list=queryset, per_page=per_page)
    return paginator.get_page(number=page_number)


async def add_complaint(user_id: uuid.UUID, payload: ComplaintRequest) -> bool:
    try:
        await Complaint.objects.acreate(
            vacancy_id=payload.vacancy,
            author_id=user_id,
            reason=payload.reason,
            details=payload.details,
        )
        return True
    except IntegrityError:
        return False


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

    raw_salary_min = params.get("salary_min")
    raw_salary_min = int(raw_salary_min) if raw_salary_min else 0
    queryset = filter_services.apply_salary_filters(queryset, raw_salary_min)

    for filter_key, db_field in FILTER_MAPPING.items():
        filter_data = params.get(filter_key, {})
        if filter_data:
            queryset = filter_services.apply_dynamic_filter(
                queryset, db_field, filter_data
            )

    sort_by = params.get("sort", "date")
    queryset = filter_services.apply_sorting(queryset, sort_by)

    return queryset.prefetch_related("skills")


def get_similar_vacancies(
    vacancy_id: uuid.UUID, limit: int = 12
) -> QuerySet["Vacancy"]:
    """
    Selects similar active vacancies based on the matching of the name and common skills
    """

    cache_key = f"similar_vacancies_{vacancy_id}"
    cached_ids = cache.get(cache_key)

    if cached_ids is not None:
        if not cached_ids:
            return Vacancy.objects.none()
        preserved_order = Case(
            *[When(id=pk, then=pos) for pos, pk in enumerate(cached_ids)]
        )
        return Vacancy.objects.filter(id__in=cached_ids).order_by(preserved_order)

    try:
        base_vacancy = Vacancy.objects.prefetch_related("skills").get(id=vacancy_id)
    except Vacancy.DoesNotExist:
        logger.warning(
            f"Attempted to find similar for non-existent vacancy ID: {vacancy_id}"
        )
        return Vacancy.objects.none()

    period = timezone.now() - timedelta(days=30)
    skill_ids = list(base_vacancy.skills.values_list("id", flat=True))

    similar_qs = (
        Vacancy.objects.filter(status=Vacancy.Status.ACTIVE, published_at__gt=period)
        .exclude(id=base_vacancy.id)
        .annotate(
            title_sim=TrigramSimilarity("title", base_vacancy.title),
            shared_skills=Count("skills", filter=Q(skills__in=skill_ids)),
        )
        .filter(Q(title_sim__gt=0.15) | Q(shared_skills__gt=0))
        .order_by(
            "-title_sim",
            "-shared_skills",
            "-published_at",
        )[:limit]
    )

    similar_ids = list(similar_qs.values_list("id", flat=True))
    cache.set(cache_key, similar_ids, timeout=11800)

    return similar_qs


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

    all_vacancies = get_active_vacancies()
    vacancies_per_month = all_vacancies.count()
    today = timezone.now().date()
    vacancies_today = all_vacancies.filter(published_at__date=today).count()

    return {
        "work_formats": Vacancy.WorkFormat.choices,
        "grades": Vacancy.Grade.choices,
        "employment_types": Vacancy.EmploymentType.choices,
        "skills": skills,
        "geo": {
            "regions": regions,
            "countries": countries,
            "cities": cities,
        },
        "vacancies_per_month": vacancies_per_month,
        "vacancies_today": vacancies_today,
    }
