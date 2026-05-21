import uuid

from core.models import SluggedMixin, TimeStampedMixin
from django.db import models


class Company(TimeStampedMixin):
    """
    It is provided separately for the analysis and dedublication of records.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Company ID"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Company name",
        help_text="Original name, fetched from vacancy",
    )
    normalized_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Normalized name",
        help_text="Lower case without spaces. Using for search duplicates",
    )

    class Meta:
        db_table = "vacancies_company"
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name and not self.normalized_name:
            self.normalized_name = self.name.lower().replace(" ", "")

        super().save(*args, **kwargs)


class Location(TimeStampedMixin):
    """
    It will contain locations of different levels (regions, countries, cities)
    """

    id = models.AutoField(primary_key=True, editable=False)
    region = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Macroregion",
        help_text="For example: CIS(СНГ), Europe, Asia",
    )
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "vacancies_location"
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ["id"]

    def __str__(self):
        parts = [self.country, self.region, self.city]
        valid_parts = [part for part in parts if part]
        return ", ".join(valid_parts) if valid_parts else "Unknown Location"


class Skill(TimeStampedMixin, SluggedMixin):
    """
    It is provided separately for the filtering vacancies by skills and dedublication of records
    """

    id = models.AutoField(primary_key=True, editable=False, verbose_name="Skill ID")

    class Meta:
        db_table = "vacancies_skill"
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkFormat(TimeStampedMixin, SluggedMixin):
    """
    It is provided separately for the filtering vacancies by work format and dedublication of records
    """

    id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        db_table = "vacancies_work_format"
        verbose_name = "Work Format"
        verbose_name_plural = "Work Formats"

    def __str__(self):
        return self.name


class Contact(TimeStampedMixin):
    """
    It is taken out for convenience. Because a vacancy can have from 1 to 3 contacts
    """

    class Platform(models.TextChoices):
        TELEGRAM = "TG", "Telegram"
        DISCORD = "DS", "Discord"
        EMAIL = "EM", "Email"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Contact ID"
    )
    platform = models.CharField(max_length=2, choices=Platform.choices)
    details = models.CharField(
        max_length=100,
        verbose_name="Contact link",
        help_text="For example: @example, example@example.example",
    )

    class Meta:
        db_table = "vacancies_contact"
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_platform_display()}: {self.details}"


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

    class EnglishLevel(models.TextChoices):
        NOT_REQUIRED = "NS", "Not specified"
        A1 = "A1", "A1 (Beginner)"
        A2 = "A2", "A2 (Elementary)"
        B1 = "B1", "B1 (Intermediate)"
        B2 = "B2", "B2 (Upper-Intermediate)"
        C1 = "C1", "C1 (Advanced)"
        C2 = "C2", "C2 (Proficient)"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Vacancy ID"
    )
    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
    )
    autor = models.ForeignKey(
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

    title = models.CharField(max_length=255)
    description = models.TextField(verbose_name="Description (cleared)")

    salary_min = models.IntegerField(null=True, blank=True, verbose_name="Salary from")
    usd_salary_min = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Salary from (Converted in USD)",
    )
    salary_max = models.IntegerField(null=True, blank=True, verbose_name="Salary up to")
    currency = models.CharField(max_length=3, null=True, blank=True)

    status = models.CharField(
        max_length=3, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    grade = models.CharField(
        max_length=3, choices=Grade.choices, null=True, blank=True, db_index=True
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
    work_formats = models.ManyToManyField(
        "WorkFormat", related_name="vacancies", blank=True
    )

    views_count = models.IntegerField(default=0)
    contacts_opened_count = models.IntegerField(default=0)

    contact = models.ManyToManyField("Contact", related_name="vacancies")

    content_hash = models.CharField(
        max_length=64, unique=True, verbose_name="Hash of the content"
    )
    published_at = models.DateField(db_index=True, verbose_name="Published date")

    class Meta:
        db_table = "vacancies_vacancy"
        verbose_name = "Vacancy"
        verbose_name_plural = "Vacancies"
        ordering = ["-published_at"]

        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["grade", "-published_at"]),
            models.Index(fields=["usd_salary_min", "-published_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
