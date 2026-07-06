from collections import defaultdict
from typing import Any

from django.db.models import Count, QuerySet
from django.db.models.functions import TruncDate

from apps.vacancies.models import Vacancy

from .models import GlobalAnalyticsSnapshot


async def aget_last_analytics() -> GlobalAnalyticsSnapshot | None:
    return await GlobalAnalyticsSnapshot.objects.order_by("-created_at").afirst()


async def acalculate_analytics(queryset: QuerySet[Vacancy]) -> dict[str, Any]:
    per_day_qs = (
        queryset.annotate(day=TruncDate("published_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    vacancies_per_day = [
        {"day": item["day"].isoformat() if item["day"] else "", "count": item["count"]}
        async for item in per_day_qs
    ]

    grades_qs = (
        queryset.filter(grade__isnull=False).values("grade").annotate(count=Count("id"))
    )
    grades_distribution = defaultdict(int)
    grade_mapping = dict(Vacancy.Grade.choices)

    async for item in grades_qs:
        grade_code = item["grade"]
        label = grade_mapping.get(grade_code)
        if label:
            grades_distribution[label] += item["count"]

    exp_qs = (
        queryset.filter(experience_from__isnull=False)
        .values("experience_from")
        .annotate(count=Count("id"))
    )
    experience_funnel = defaultdict(int)

    async for item in exp_qs:
        exp_val = item["experience_from"]
        label = str(exp_val)
        experience_funnel[label] += item["count"]

    format_qs = (
        queryset.filter(work_format__isnull=False)
        .values("work_format")
        .annotate(count=Count("id"))
    )
    work_formats = defaultdict(int)
    format_mapping = dict(Vacancy.WorkFormat.choices)

    async for item in format_qs:
        format_code = item["work_format"]
        label = format_mapping.get(format_code)
        if label:
            work_formats[label] += item["count"]

    skills_qs = (
        queryset.filter(skills__isnull=False)
        .values("skills__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    top_skills = [
        {"skill": item["skills__name"], "count": item["count"]}
        async for item in skills_qs
    ]

    return {
        "top_skills": top_skills,
        "work_formats": dict(work_formats),
        "experience_funnel": dict(experience_funnel),
        "grades_distribution": dict(grades_distribution),
        "vacancies_per_day": vacancies_per_day,
    }
