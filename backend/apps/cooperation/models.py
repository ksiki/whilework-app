import uuid6
from core.models import TimeStampedMixin
from django.db import models


class Message(TimeStampedMixin):
    id = models.UUIDField(
        primary_key=True, default=uuid6.uuid7, editable=False, verbose_name="Message ID"
    )
    name = models.CharField(max_length=125, default="Anonym")
    email = models.EmailField(db_index=True)
    text = models.TextField()

    class Meta:
        db_table = "cooperations_message"
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.email}, created at: {self.created_at.strftime('%Y-%m-%d')}"
