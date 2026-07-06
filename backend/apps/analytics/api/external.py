import hashlib
import json
import logging

from django.core.cache import cache
from django.http import HttpRequest
from ninja import Query, Router

from apps.analytics import services
from apps.vacancies import services as vacancies_services

from .schemas import AnalyticsQuerySchema, AnalyticsResponse

logger = logging.getLogger(__name__)

router = Router(tags=["Analytics API"])


def generate_analytics_cache_key(filters: dict | None, user_id: int | None) -> str:
    """Генерирует уникальный ключ для кеша на основе фильтров и ID пользователя."""
    filter_str = json.dumps(filters, sort_keys=True) if filters else "no_filters"
    hash_payload = f"user:{user_id}_filters:{filter_str}"
    return "analytics_" + hashlib.md5(hash_payload.encode()).hexdigest()


def is_effectively_empty(filters: dict) -> bool:
    """
    Проверяет, содержит ли словарь фильтров только дефолтные значения.
    """
    if not filters:
        return True

    if filters.get("search", {}).get("query"):
        return False

    if filters.get("experience_from") or filters.get("salary_min"):
        return False

    list_keys = ["sources", "work_type", "work_format", "grade", "skills", "geo"]
    for key in list_keys:
        if filters.get(key, {}).get("items"):
            return False

    relocation = filters.get("relocation", {})
    if relocation.get("any") or relocation.get("items"):
        return False

    return True


@router.get(
    "/calculate/",
    response={200: AnalyticsResponse, 404: dict, 500: dict},
)
async def calculate(request: HttpRequest, query: AnalyticsQuerySchema = Query(...)):
    try:
        filters_dict = query.filters if query.filters else {}
        if is_effectively_empty(filters_dict):
            last_analytics = await services.aget_last_analytics()

            if not last_analytics:
                return 404, {"message": "Analytics not found"}

            return 200, last_analytics

        user = await request.auser()
        user_id = user.id if user.is_authenticated else None

        filters_dict = query.filters if query.filters else {}
        cache_key = generate_analytics_cache_key(filters_dict, user_id)

        cached_result = await cache.aget(cache_key)
        if cached_result:
            return 200, cached_result

        vacancies = vacancies_services.get_active_vacancies()
        blacklist = None

        if user.is_authenticated:
            blacklist_qs = user.company_blacklist.values_list("id", flat=True)
            blacklist = [company_id async for company_id in blacklist_qs]

        vacancies = vacancies_services.apply_filters(
            queryset=vacancies,
            blacklist_companies=blacklist,
            params=filters_dict,
        )

        result = await services.acalculate_analytics(queryset=vacancies)
        await cache.aset(cache_key, result, timeout=1800)

        return 200, result
    except Exception as e:
        logger.error("Failed to calculate analytics: %s", e, exc_info=True)
        return 500, {"message": "Internal server error during calculation"}
