import logging

from django.contrib.auth import authenticate, get_user_model, login
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from ninja import Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.accounts import services
from apps.accounts.api.schemas import (
    CompanyBlacklistRequest,
    LoginRequest,
    ReadNotificationRequest,
    RegisterRequest,
    SuccessResponse,
    VerifyOTPRequest,
)

logger = logging.getLogger(__name__)
router = Router(
    tags=["Accounts API"],
    throttle=[AnonRateThrottle("50/m"), AuthRateThrottle("50/m")],
)
User = get_user_model()


@router.post("/register/", response={200: SuccessResponse, 400: dict})
def register_user(request: HttpRequest, payload: RegisterRequest) -> HttpResponse:
    email = payload.email

    user = User.objects.filter(email=email).first()

    if user:
        if user.is_active:
            return 400, {
                "error": "The user with this email already exists",
                "i18n": "email_already_exists",
            }

        user.set_password(payload.password)
        user.save()
    else:
        user = User.objects.create_user(
            email=email, password=payload.password, is_active=False
        )

    otp_sent = services.OTPAuthService.generate_and_send_otp(email)

    if not otp_sent:
        logger.error(f"Failed to send OTP to {email}")
        return 400, {
            "error": "Couldn't send the code to the mail. Try again later",
            "i18n": "сould_not_send_code_to_mail",
        }

    return 200, {
        "success": True,
        "message": "The code has been sent to emai",
        "i18n": "code_has_been_sent_to_emai",
    }


@router.post("/verify/", response={200: SuccessResponse, 400: dict})
def verify_otp(request: HttpRequest, payload: VerifyOTPRequest) -> HttpResponse:
    email = payload.email

    is_valid = services.OTPAuthService.verify_otp_code(email, payload.code)

    if not is_valid:
        return 400, {"error": "Invalid or outdated code.", "i18n": "invalid_code"}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return 400, {"error": "The user was not found.", "i18n": "user_not_found"}

    user.is_active = True
    user.save()

    login(request, user)

    return 200, {
        "success": True,
        "message": "Registration has been completed successfully.",
        "i18n": "registration_completed_successfully",
    }


@router.post("/login/", response={200: SuccessResponse, 400: dict})
def login_user(request: HttpRequest, payload: LoginRequest) -> HttpResponse:
    user = authenticate(request, username=payload.email, password=payload.password)

    if user is None:
        return 400, {
            "error": "Invalid email or password.",
            "i18n": "invalid_email_or_password",
        }

    if not user.is_active:
        services.OTPAuthService.generate_and_send_otp(user.email)
        return 400, {
            "error": "Your account has not been activated. We have sent a new OTP code to your email.",
            "i18n": "account_not_activated",
        }

    login(request, user)

    return 200, {
        "success": True,
        "message": "Authorization is successful.",
        "i18n": "authorization_successful",
    }


@router.post(
    "/blacklist/companies/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
def edit_companies_blacklist(
    request: HttpRequest, payload: CompanyBlacklistRequest
) -> HttpResponse:
    try:
        message = services.edit_blacklist(
            user=request.user, company_id=payload.company_id, delete=payload.delete
        )
    except IntegrityError:
        return 400, {"error": "The company was not found"}

    return 200, {
        "success": True,
        "message": message,
        "i18n": "",
    }


@router.post(
    "/notification/read/",
    auth=django_auth,
    response={200: SuccessResponse, 404: dict},
)
def read_notification(request: HttpRequest, payload: ReadNotificationRequest):
    try:
        services.mark_notification_as_read(
            user_id=request.user.id, notif_id=payload.notification_id
        )
    except ObjectDoesNotExist:
        return 404, {"error": "The notification was not found"}

    return 200, {
        "success": True,
        "message": "The notification has been read",
        "i18n": "",
    }
