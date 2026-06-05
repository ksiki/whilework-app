import logging
import secrets
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail

from .models import User as UserModel

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
