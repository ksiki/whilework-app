from core.models import TimeStampedMixin
from django.db import models


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

        constraints = [
            models.UniqueConstraint(
                fields=["region", "country", "city"], name="unique_location"
            )
        ]

    def __str__(self):
        parts = [self.country, self.region, self.city]
        valid_parts = [part for part in parts if part]
        return ", ".join(valid_parts) if valid_parts else "Unknown Location"
