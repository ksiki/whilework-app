from core.models import TimeStampedMixin
from django.db import models


class Report404(TimeStampedMixin):
    url = models.CharField(max_length=255)

    class Meta:
        db_table = "system_report404"
        verbose_name = "Report404"
        verbose_name_plural = "Reports404"
        ordering = ["-created_at"]

    def __str__(self):
        return self.url


class Currency(TimeStampedMixin):
    iso = models.CharField(max_length=3, verbose_name="ISO code")
    currency_rate = models.FloatField(default=0)

    class Meta:
        db_table = "system_currency"
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.iso}: {self.currency_rate}"
