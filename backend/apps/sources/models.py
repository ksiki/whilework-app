import uuid

from core.models import TimeStampedMixin
from django.db import models


class Source(TimeStampedMixin):
    class Platform(models.TextChoices):
        DISCORD = "DIS", "Discord"
        TELEGRAM = "TLG", "Telegram"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Source ID"
    )

    platform = models.CharField(
        max_length=3, choices=Platform.choices, verbose_name="Platform name"
    )
    name = models.CharField(max_length=255, verbose_name="Source name")
    identifier = models.CharField(
        max_length=255,
        unique=True,
        help_text="Channel ID, link, or snowflake in Discord (which is what the parser is looking for)",
    )

    is_active = models.BooleanField(default=True)

    last_parsed_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID of the last processed message (for Airflow)",
    )

    error_count = models.IntegerField(default=0)
    last_error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "sources_source"
        verbose_name = "Source"
        verbose_name_plural = "Sources"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()}) - {'Active' if self.is_active else 'Inactive'}"
