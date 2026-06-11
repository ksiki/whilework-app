import logging
import secrets
import uuid
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils import timezone

from .models import User as UserModel
from .models import UserNotification

logger = logging.getLogger(__name__)
User = get_user_model()


class OTPAuthService:
    OTP_EXPIRY_TIMEOUT = 300

    @staticmethod
    def _generate_otp_code() -> str:
        return str(secrets.randbelow(9000) + 1000)

    @classmethod
    def generate_and_send_otp(cls, email: str) -> bool:
        """
        Generates a code, stores it in a cache linked to an email and sends it to the mail.
        """
        otp_code = cls._generate_otp_code()
        cache_key = f"otp_register_{email}"
        cache.set(cache_key, otp_code, timeout=cls.OTP_EXPIRY_TIMEOUT)

        try:
            subject = "Registration confirmation code| WHILEWORK"
            message = f"Your code to complete the registration: {otp_code}\nThe code is valid for 5 minutes."

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Error sending OTP to email{email}: {e}")
            return False

    @classmethod
    def verify_otp_code(cls, email: str, code_to_verify: str) -> bool:
        cache_key = f"otp_register_{email}"
        saved_code = cache.get(cache_key)

        if not saved_code:
            return False

        if secrets.compare_digest(str(saved_code), str(code_to_verify)):
            cache.delete(cache_key)
            return True

        return False


def get_profile_data(email: str) -> dict[str, Any]:
    user = UserModel.objects.get(email=email)
    user_notifs = user.user_notifications.select_related("notification").all()
    black_list = user.company_blacklist.all()
    return {
        "user_id": user.id,
        "email": email,
        "available_slots": user.available_slots,
        "notifications": user_notifs,
        "blacklist": black_list,
    }


async def edit_blacklist(user: UserModel, company_id: uuid.UUID, delete: bool) -> bool:
    if delete:
        await user.company_blacklist.aremove(company_id)
        message = "Company removed from blacklist"
    else:
        await user.company_blacklist.aadd(company_id)
        message = "Company added to blacklist"
    return message


def mark_notification_as_read(user_id: uuid.UUID, notif_id: uuid.UUID) -> None:
    updated_count = UserNotification.objects.filter(
        user_id=user_id, notification_id=notif_id
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )
    if updated_count == 0:
        raise ObjectDoesNotExist("Notification not found")


async def update_viewed_vacancies(user: UserModel, vacancy_id: uuid.UUID) -> bool:
    try:
        await user.viewed_vacancies.aadd(vacancy_id)
        return True
    except Exception:
        return False
