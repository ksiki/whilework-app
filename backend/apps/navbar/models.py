import uuid6
from core.models import TimeStampedMixin
from django.db import models


class SupportMessage(TimeStampedMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid6.uuid7,
        editable=False,
        verbose_name="Support Message ID",
    )

    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_messages",
    )

    title = models.CharField(max_length=250, blank=True)
    message = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "navbar_support_message"
        verbose_name = "SupportMessage"
        verbose_name_plural = "SupportMessages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Support Message {self.id} on User: {self.author.id}"
