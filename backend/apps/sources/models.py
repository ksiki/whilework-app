import uuid6
from core.models import TimeStampedMixin
from django.db import models


class Source(TimeStampedMixin):
    class Platform(models.TextChoices):
        DISCORD = "DIS", "Discord"
        TELEGRAM = "TLG", "Telegram"

    id = models.UUIDField(
        primary_key=True, default=uuid6.uuid7, editable=False, verbose_name="Source ID"
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
        help_text="ID of the last processed message (for Parser)",
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

    @property
    def has_topics(self) -> bool:
        return self.topics.filter(is_active=True).exists()


class SourceTopic(TimeStampedMixin):
    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    source = models.ForeignKey(
        "Source",
        on_delete=models.CASCADE,
        related_name="topics",
        verbose_name="Parent Source",
    )
    topic_id = models.CharField(
        max_length=255, help_text="Branch ID in Telegram or Discord"
    )

    is_active = models.BooleanField(default=True)

    last_parsed_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The ID of the last processed message in this particular topic",
    )
    error_count = models.IntegerField(default=0)
    last_error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "sources_source_topic"
        verbose_name = "Source Topic"
        verbose_name_plural = "Source Topics"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "topic_id"], name="unique_source_topic"
            )
        ]

    def __str__(self):
        return f"{self.source.name} - Topic: {self.topic_id} ({'Active' if self.is_active else 'Inactive'})"
