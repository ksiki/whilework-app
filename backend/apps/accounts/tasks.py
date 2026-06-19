import logging

from core.broker import broker
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@broker.task
def send_otp_email_task(email: str, otp_code: str) -> None:
    try:
        subject = "Registration confirmation code | WHILEWORK"
        message = f"Your code to complete the registration: {otp_code}\nThe code is valid for 5 minutes."

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"OTP email successfully sent to {email}")
    except Exception as e:
        logger.error(f"Error sending OTP to email {email}: {e}")
        raise e
