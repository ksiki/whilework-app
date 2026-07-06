import uuid6
from core.models import SluggedMixin, TimeStampedMixin
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Company(SluggedMixin, TimeStampedMixin):
    """
    It is provided separately for the analysis and dedublication of records.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid6.uuid7, editable=False, verbose_name="Company ID"
    )

    class Meta:
        db_table = "vacancies_company"
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

        indexes = [
            GinIndex(
                name="company_name_gin", fields=["name"], opclasses=["gin_trgm_ops"]
            ),
        ]

    def __str__(self):
        return self.name
