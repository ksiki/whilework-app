import uuid6
from core.models import TimeStampedMixin
from django.db import models


class ParserRawMessage(TimeStampedMixin):
    """
    Storage of dirty vacancies before parsing
    """

    class Status(models.TextChoices):
        PENDING = "PND", "Pending"
        PROCESSED = "PRC", "Processed"
        FAILED = "FLD", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid6.uuid7,
        editable=False,
        verbose_name="Raw Message ID",
    )
    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.CASCADE,
        related_name="parsed_raw_messages",
        verbose_name="Source ID",
    )
    topic = models.ForeignKey(
        "sources.SourceTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_messages",
    )

    external_msg_id = models.CharField(
        max_length=255,
        verbose_name="External Message ID",
        help_text="The ID of the message in the source",
    )
    raw_text = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=3, default=Status.PENDING, choices=Status.choices
    )

    class Meta:
        db_table = "inbox_parsed_raw_message"
        verbose_name = "Parsed Raw Message"
        verbose_name_plural = "Parsed Raw Messages"
        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_msg_id"], name="unique_source_message"
            )
        ]

    def __str__(self):
        return f"Msg {self.external_msg_id} (Source ID: {self.source_id}) - {self.get_status_display()}"
