import nh3
import uuid6
from core.models import TimeStampedMixin
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.urls import reverse
from slugify import slugify


class Vacancy(TimeStampedMixin):
    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        CLOSED = "CLS", "Closed"
        ARCHIVED = "ARC", "Archive"

    class Grade(models.TextChoices):
        INTERN = "INT", "Intern"
        JUNIOR = "JUN", "Junior"
        MIDDLE = "MID", "Middle"
        SENIOR = "SEN", "Senior"
        LEAD = "LED", "Lead"
        DIRECTOR = "DIR", "Director"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "FT", "Full day"
        PART_TIME = "PT", "Part-time employment"
        PROJECT = "PRJ", "Project"

    class WorkFormat(models.TextChoices):
        REMOTE = "RMT", "Remote"
        OFFICE = "OFF", "Office"
        HYBRID = "HBR", "Hybrid"

    class EnglishLevel(models.TextChoices):
        A1 = "A1", "A1 (Beginner)"
        A2 = "A2", "A2 (Elementary)"
        B1 = "B1", "B1 (Intermediate)"
        B2 = "B2", "B2 (Upper-Intermediate)"
        C1 = "C1", "C1 (Advanced)"
        C2 = "C2", "C2 (Proficient)"

    id = models.UUIDField(
        primary_key=True, default=uuid6.uuid7, editable=False, verbose_name="Vacancy ID"
    )
    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
    )

    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
    )
    location = models.ForeignKey(
        "Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
    )
    relocation = models.ForeignKey(
        "Relocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(verbose_name="Description (cleared)")

    salary_min = models.IntegerField(null=True, blank=True, verbose_name="Salary from")
    usd_salary_min = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Salary from (USD)",
        help_text="Converted in USD for search by salary min",
    )
    salary_max = models.IntegerField(null=True, blank=True, verbose_name="Salary up to")
    currency = models.CharField(max_length=3, null=True, blank=True)

    status = models.CharField(
        max_length=3, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    grade = models.CharField(
        max_length=3, choices=Grade.choices, null=True, blank=True, db_index=True
    )
    experience_from = models.IntegerField(
        null=True, blank=True, db_index=True, verbose_name="Experience from"
    )
    employment_type = models.CharField(
        max_length=3,
        choices=EmploymentType.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    english_level = models.CharField(
        max_length=2, choices=EnglishLevel.choices, null=True, blank=True, db_index=True
    )

    skills = models.ManyToManyField("Skill", related_name="vacancies", blank=True)
    work_format = models.CharField(
        max_length=3,
        choices=WorkFormat.choices,
        null=True,
        blank=True,
        db_index=True,
    )

    views_count = models.IntegerField(default=0)
    contacts_opened_count = models.IntegerField(default=0)

    contact = models.ManyToManyField("Contact", related_name="vacancies")

    content_hash = models.CharField(
        max_length=64, unique=True, verbose_name="Hash of the content"
    )
    published_at = models.DateTimeField(db_index=True, verbose_name="Published date")

    class Meta:
        db_table = "vacancies_vacancy"
        verbose_name = "Vacancy"
        verbose_name_plural = "Vacancies"
        ordering = ["-published_at"]

        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["grade", "-published_at"]),
            models.Index(fields=["usd_salary_min", "-published_at"]),
            GinIndex(
                name="vacancy_title_gin",
                fields=["title"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        ALLOWED_TAGS = {
            "p",
            "h2",
            "h3",
            "h4",
            "ul",
            "ol",
            "li",
            "strong",
            "em",
            "b",
            "i",
            "br",
        }
        if self.description:
            self.description = nh3.clean(self.description, tags=ALLOWED_TAGS)
        super().save(*args, **kwargs)

    @property
    def salary_string(self) -> str:
        if not self.salary_min and not self.salary_max:
            return ""

        currency_str = self.currency if self.currency else ""

        def format_salary(value: int) -> str:
            return f"{value:_}".replace("_", " ")

        if self.salary_min and self.salary_max:
            result = f"{format_salary(self.salary_min)} – {format_salary(self.salary_max)} {currency_str}"
        elif self.salary_min:
            result = f"{format_salary(self.salary_min)} {currency_str}"
        else:
            result = f"{format_salary(self.salary_max)} {currency_str}"

        return result.strip()

    @property
    def meta_string(self) -> str | None:
        parts = []

        if self.company:
            parts.append(self.company.name)

        if self.location_id:
            loc_parts = [
                self.location.region,
                self.location.country,
                self.location.city,
            ]
            parts.extend([p for p in loc_parts if p])

        return " | ".join(parts) if parts else None

    @property
    def seo_title(self) -> str:
        company_part = f", {self.company.name}" if self.company else ""
        base_title = f"{self.title}{company_part}"

        geo_parts = []
        if self.work_format:
            geo_parts.append(self.get_work_format_display())
        if self.location and getattr(self.location, "city", None):
            geo_parts.append(self.location.city)

        geo_string = f", {', '.join(geo_parts)}" if geo_parts else ""

        salary = self.salary_string
        salary_part = f" — {salary}" if salary else ""

        return f"{base_title}{geo_string}{salary_part}"

    @property
    def slug(self) -> str:
        company_name = self.company.name if self.company else ""
        return slugify(f"{self.title} {company_name}")

    def get_absolute_url(self) -> str:
        return reverse("web:vacancy_detail", kwargs={"id": self.id, "slug": self.slug})
