import uuid6
from core.models import TimeStampedMixin
from django.db import models


class Suggest(TimeStampedMixin):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        PLANNED = "PLN", "Planned"
        REVIEW = "RVW", "Review"
        MODERATION = "MDR", "Moderation"
        ARCHIVED = "ARC", "Archive"

    id = models.UUIDField(
        primary_key=True, default=uuid6.uuid7, editable=False, verbose_name="Suggest ID"
    )

    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.MODERATION,
        blank=True,
        db_index=True,
    )

    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggests",
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    likes = models.IntegerField(null=False, default=0)
    liked_by = models.ManyToManyField(
        "accounts.User",
        blank=True,
        related_name="liked_suggests",
    )

    class Meta:
        db_table = "community_suggest"
        verbose_name = "Suggest"
        verbose_name_plural = "Suggests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ProductionLog(TimeStampedMixin):
    class Type(models.TextChoices):
        FEAT = "FEAT", "FEAT"
        FIX = "FIX", "FIX"
        INIT = "INIT", "INIT"

    description = models.TextField()
    type = models.CharField(
        max_length=4,
        choices=Type.choices,
    )

    class Meta:
        db_table = "community_production_log"
        verbose_name = "ProductionLog"
        verbose_name_plural = "Production Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at} ({self.get_type_display()})"
