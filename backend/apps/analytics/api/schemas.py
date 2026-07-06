from typing import Any, Dict, Optional

from ninja import Schema
from pydantic import Json


class AnalyticsQuerySchema(Schema):
    filters: Optional[Json[Dict[str, Any]]] = None


class SkillItemSchema(Schema):
    skill: str
    count: int


class VacancyDaySchema(Schema):
    day: str
    count: int


class AnalyticsResponse(Schema):
    top_skills: list[SkillItemSchema]
    work_formats: Dict[str, int]
    experience_funnel: Dict[str, int]
    grades_distribution: Dict[str, int]
    vacancies_per_day: list[VacancyDaySchema]
