import uuid6
from core.models import TimeStampedMixin
from django.db import models


class Complaint(TimeStampedMixin):
    class Reason(models.TextChoices):
        SCAM = "SCM", "Scam / Fraud"
        WRONG_SALARY = "SAL", "Fake salary"
        UNRESPONSIVE = "UNR", "Employer is unresponsive"
        OTHER = "OTH", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid6.uuid7,
        editable=False,
        verbose_name="Complaint ID",
    )

    vacancy = models.ForeignKey(
        "Vacancy",
        on_delete=models.CASCADE,
        related_name="complaints",
        verbose_name="Vacancy",
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
        verbose_name="Complainant",
    )

    reason = models.CharField(
        max_length=3, choices=Reason.choices, db_index=True, verbose_name="Reason"
    )
    details = models.TextField(null=True, blank=True, verbose_name="Details")

    class Meta:
        db_table = "vacancies_complaint"
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Complaint {self.id} on {self.vacancy.title} ({self.get_reason_display()})"
        )
