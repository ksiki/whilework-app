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
