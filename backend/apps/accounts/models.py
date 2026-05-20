import uuid

from core.models import TimeStampedMixin
from django.db import models


class User(TimeStampedMixin):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="User ID"
    )

    email = models.EmailField()
    password = models.CharField(max_length=128)

    available_slots = models.IntegerField(
        default=0, help_text="The number of available slots for job placement"
    )

    company_blacklist = models.ManyToManyField(
        "vacancies.Company", related_name="users", blank=True
    )

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.email}, register: {self.created_at}, available slots: {self.available_slots}, last activity: {self.last_active_at}"


class Notification(TimeStampedMixin):
    d = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Notification ID",
    )
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="notifications"
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "accounts_notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["created_at"]

    def __str__(self):
        return f"iser id: {self.user_id}, created at: {self.created_at}, is read: {self.is_read}"


class SlotTransaction(TimeStampedMixin):
    class PaymentStatus(models.TextChoices):
        SECCESSFULLY = "SCS", "Seccessfully"
        EXPECTATION = "EXP", "Expectation"
        CANCEL = "CNC", "Cancel"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Transaction ID",
    )
    user = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="slot_transactions",
    )

    slots_added = models.IntegerField(help_text="Number of slots purchased")
    payment_status = models.CharField(max_length=3, choices=PaymentStatus.choices)

    class Meta:
        db_table = "accounts_slot_transaction"
        verbose_name = "Slot Transaction"
        verbose_name_plural = "Slot Transactions"
        ordering = ["created_at"]

    def __str__(self):
        return f"iser id: {self.user_id}, created at: {self.created_at}, is read: {self.is_read}"
