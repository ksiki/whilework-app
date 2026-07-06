from core.models import TimeStampedMixin
from django.db import models


class Relocation(TimeStampedMixin):
    id = models.AutoField(primary_key=True, editable=False)
    country = models.CharField(max_length=100, null=True, blank=True, unique=True)

    class Meta:
        db_table = "vacancies_relocation"
        verbose_name = "Relocation"
        verbose_name_plural = "Relocations"
        ordering = ["id"]

    def __str__(self):
        return f"Relocate to {self.country}"
