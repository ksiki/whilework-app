import logging
from typing import Any

from django.db.models import Q, QuerySet

from .models import Vacancy

logger = logging.getLogger(__name__)


def _apply_q_object(queryset: QuerySet, q_obj: Q, mode: str | None) -> QuerySet:
    if mode == "exclude":
        return queryset.exclude(q_obj)
    return queryset.filter(q_obj)


def apply_text_search(
    queryset: QuerySet["Vacancy"], search_data: dict[str, Any]
) -> QuerySet["Vacancy"]:
    query = search_data.get("query", "").strip()
    fields = search_data.get("fields", [])

    if not query or not fields:
        return queryset

    search_filter = Q()
    if "title" in fields:
        search_filter |= Q(title__icontains=query)
    if "company" in fields:
        search_filter |= Q(company__name__icontains=query)
    if "skills" in fields:
        search_filter |= Q(skills__name__icontains=query)

    try:
        return queryset.filter(search_filter)
    except Exception as e:
        logger.error(
            f"Search filtering error. Query: {query}; Fields: {fields}; E: {e}"
        )
        return queryset


def apply_geo_filters(
    queryset: QuerySet["Vacancy"], geo_data: dict[str, Any]
) -> QuerySet["Vacancy"]:
    items = geo_data.get("items", [])
    if not items:
        return queryset

    category = geo_data.get("category")
    mode = geo_data.get("mode")

    geo_field_map = {
        "regions": "location__region__in",
        "countries": "location__country__in",
        "cities": "location__city__in",
    }

    db_field = geo_field_map.get(category)
    if not db_field:
        return queryset

    return _apply_q_object(queryset, Q(**{db_field: items}), mode)


def apply_source_filters(
    queryset: QuerySet["Vacancy"], sources_data: dict[str, Any]
) -> QuerySet["Vacancy"]:
    items = sources_data.get("items", [])
    if not items:
        return queryset

    mode = sources_data.get("mode")

    q_obj = Q()
    for item in items:
        if item == "whilework":
            q_obj |= Q(author__isnull=False)
        else:
            q_obj |= Q(sources__platform=item)

    return _apply_q_object(queryset, q_obj, mode)


def apply_dynamic_filter(
    queryset: QuerySet["Vacancy"], db_field: str, filter_data: dict[str, Any]
) -> QuerySet["Vacancy"]:
    items = filter_data.get("items", [])
    if not items:
        return queryset

    logic = filter_data.get("logic", "and")
    mode = filter_data.get("mode", "choose")

    if logic == "or":
        q_obj = Q(**{f"{db_field}__in": items})
        queryset = _apply_q_object(queryset, q_obj, mode)
    elif logic == "and":
        for item in items:
            q_obj = Q(**{db_field: item})
            queryset = _apply_q_object(queryset, q_obj, mode)

    return queryset


def apply_sorting(queryset: QuerySet["Vacancy"], sort_by: str) -> QuerySet["Vacancy"]:
    if sort_by == "salary":
        return queryset.order_by("-salary_from", "-published_at")
    return queryset.order_by("-published_at")
