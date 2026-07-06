from core.models import SluggedMixin, TimeStampedMixin
from django.contrib.postgres.indexes import GinIndex
from django.db import models


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

        indexes = [
            GinIndex(
                name="skill_name_gin", fields=["name"], opclasses=["gin_trgm_ops"]
            ),
        ]

    def __str__(self):
        return self.name
