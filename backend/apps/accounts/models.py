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
        return f"{self.email}, register: {self.created_at}, available slots: {self.available_slots}"


class Notification(TimeStampedMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Notification ID",
    )
    users = models.ManyToManyField(
        "User",
        through="UserNotification",
        related_name="notifications",
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    class Meta:
        db_table = "accounts_notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["created_at"]

    def __str__(self):
        return self.title


class UserNotification(models.Model):
    """
    An intermediate table for tracking the read status of a notification for each user
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="User Notification ID",
    )
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="user_notifications"
    )
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="user_notifications"
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_user_notification"
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "notification"], name="unique_user_notification"
            )
        ]

    def __str__(self):
        return f"user: {self.user.email}, notification id: {self.notification_id}, read: {self.is_read}"


class SlotTransaction(TimeStampedMixin):
    class PaymentStatus(models.TextChoices):
        SUCCESS = "SCS", "Success"
        PENDING = "PND", "Pending"
        CANCELLED = "CNC", "Cancelled"

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
    payment_status = models.CharField(
        max_length=3,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    class Meta:
        db_table = "accounts_slot_transaction"
        verbose_name = "Slot Transaction"
        verbose_name_plural = "Slot Transactions"
        ordering = ["-created_at"]

    def __str__(self):
        user_email = self.user.email if self.user else "Deleted User"
        return f"email: {user_email}, slots: +{self.slots_added}"
