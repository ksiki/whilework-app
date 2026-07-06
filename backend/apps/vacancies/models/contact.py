import uuid6
from core.models import TimeStampedMixin
from django.db import models


class Contact(TimeStampedMixin):
    """
    It is taken out for convenience. Because a vacancy can have from 1 to 3 contacts
    """

    class Platform(models.TextChoices):
        TELEGRAM = "TG", "Telegram"
        DISCORD = "DS", "Discord"
        EMAIL = "EM", "Email"
        FORM = "FR", "Form"
        NUMBER = "NM", "Number"
        REDDIT = "RD", "Reddit"

    id = models.UUIDField(
        primary_key=True, default=uuid6.uuid7, editable=False, verbose_name="Contact ID"
    )
    platform = models.CharField(max_length=2, choices=Platform.choices)
    details = models.CharField(
        max_length=255,
        verbose_name="Contact link",
        help_text="For example: @example, example@example.example",
    )

    class Meta:
        db_table = "vacancies_contact"
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_platform_display()}: {self.details}"
