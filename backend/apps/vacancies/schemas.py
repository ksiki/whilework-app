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
    NUMBER = "NM"


class ContactSchema(BaseModel):
    platform: ContactPlatformEnum
    details: str


class CleanVacancySchema(BaseModel):
    reasoning: str = Field(description="Краткий анализ текста (шаг за шагом)")
    is_vacancy: bool

    title: Optional[str] = None
    description: Optional[str] = Field(
        None,
        description="Оберни в HTML, используя СТРОГО только теги: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <br>",
    )

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = Field(None, description="Код ISO (RUB, USD, EUR)")

    grade: Optional[GradeEnum] = Field(
        None,
        description="Intern->INT, Junior->JUN, Middle->MID, Senior->SEN, Lead->LED, Director/Head->DIR",
    )
    experience_from: Optional[int] = Field(None, description="Опыт в годах (число)")

    work_format: Optional[WorkFormatEnum] = None
    employment_type: Optional[EmploymentTypeEnum] = None
    english_level: Optional[EnglishLevelEnum] = Field(
        None,
        description="Beginner->A1, Elementary->A2, Intermediate->B1, Upper-Intermediate->B2, Advanced->C1",
    )

    company_name: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    relocation_country: Optional[str] = Field(
        None, description="ОБЯЗАТЕЛЬНО ТОЛЬКО ЧТО-ТО ОДНО: страна, город или регион"
    )

    skills: List[str] = Field(
        default_factory=list,
        description="Hard-skills на английском. Игнорировать soft-skills.",
    )
    contacts: List[ContactSchema] = Field(default_factory=list)
