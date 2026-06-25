from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class GradeEnum(str, Enum):
    INTERN = "INT"
    JUNIOR = "JUN"
    MIDDLE = "MID"
    SENIOR = "SEN"
    LEAD = "LED"
    DIRECTOR = "DIR"


class EmploymentTypeEnum(str, Enum):
    FULL_TIME = "FT"
    PART_TIME = "PT"
    PROJECT = "PRJ"


class WorkFormatEnum(str, Enum):
    REMOTE = "RMT"
    OFFICE = "OFF"
    HYBRID = "HBR"


class EnglishLevelEnum(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class ContactPlatformEnum(str, Enum):
    TELEGRAM = "TG"
    DISCORD = "DS"
    EMAIL = "EM"
    FORM = "FR"


class ContactSchema(BaseModel):
    platform: ContactPlatformEnum = Field(description="Тип контакта")
    details: str = Field(description="Сам контакт (ссылка, юзернейм или почта)")


class CleanVacancySchema(BaseModel):
    reasoning: str = Field(
        description="Краткий анализ текста: почему это вакансия, резюме, реклама или спам? Подумай шаг за шагом."
    )
    is_vacancy: bool = Field(
        description="True, если текст является предложением о работе от работодателя. False в любом другом случае."
    )

    title: str = Field(
        None, description="Название вакансии (чистое, без зарплаты, грейда и условий)"
    )
    description: str | None = Field(
        None,
        description="Подробное описание вакансии в HTML (разрешены теги p, h2, h3, ul, li, strong, br)",
    )

    salary_min: Optional[int] = Field(
        None, description="Минимальная зарплата (только число)"
    )
    salary_max: Optional[int] = Field(
        None, description="Максимальная зарплата (только число)"
    )
    currency: Optional[str] = Field(
        None, description="Код валюты из 3 букв (RUB, USD, EUR)"
    )

    grade: Optional[GradeEnum] = Field(
        None,
        description="Грейд специалиста. Обязательно ищи маркеры в названии вакансии или тексте! "
        "'Intern' -> INT, 'Junior' -> JUN, 'Middle' -> MID, 'Senior' -> SEN, 'Lead' -> LED, 'Director/Head' -> DIR.",
    )

    experience_from: Optional[int] = Field(
        None,
        description="Минимальный требуемый опыт работы в годах (ТОЛЬКО ЧИСЛО). "
        "Пример: '3+ года опыта' -> 3. 'Опыт от 1 до 3 лет' -> 1. 'Без опыта' -> 0.",
    )

    work_format: Optional[WorkFormatEnum] = Field(
        None,
        description="Формат работы. Ищи слова в тексте: "
        "'Удалённый формат', 'Удаленка', 'Remote' -> RMT. "
        "'Офис', 'in-office' -> OFF. "
        "'Гибрид', 'hybrid' -> HBR.",
    )

    employment_type: Optional[EmploymentTypeEnum] = Field(
        None,
        description="Тип занятости. 'Full-time', 'полная занятость' -> FT. 'Part-time', 'частичная' -> PT. 'Проектная' -> PRJ.",
    )

    english_level: Optional[EnglishLevelEnum] = Field(
        None,
        description="Минимальный уровень английского языка. Сопоставь текст с кодом: "
        "'Beginner' -> A1, 'Elementary' -> A2, 'Intermediate' -> B1, "
        "'Upper-Intermediate' -> B2, 'Advanced' -> C1, 'Proficient/Native' -> C2",
    )

    company_name: Optional[str] = Field(None, description="Название компании")

    location_region: Optional[str] = Field(None)
    location_country: Optional[str] = Field(None)
    location_city: Optional[str] = Field(None)

    skills: List[str] = Field(
        default_factory=list,
        description="Список ключевых hard-skills (технологии, языки, инструменты). "
        "СТРОГО ИГНОРИРУЙ soft-skills (внимательность к деталям, коммуникабельность, проактивность, стрессоустойчивость и т.д.).",
    )
    contacts: List[ContactSchema] = Field(
        default_factory=list, description="Найденные контакты"
    )
