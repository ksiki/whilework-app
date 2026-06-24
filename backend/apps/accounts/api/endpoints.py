import logging

from asgiref.sync import sync_to_async
from django.contrib.auth import (
    aauthenticate,
    alogin,
    get_user_model,
    login,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from ninja import Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.accounts import services
from apps.accounts.api.schemas import (
    AddViewedVacancy,
    ChangePasswordRequest,
    CompanyBlacklistRequest,
    DeleteUserRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ReadNotificationRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SuccessResponse,
    VerifyOTPRequest,
)

logger = logging.getLogger(__name__)
router = Router(
    tags=["Accounts API"],
    throttle=[AnonRateThrottle("100/m"), AuthRateThrottle("200/m")],
)
User = get_user_model()


@router.post("/register/", response={200: SuccessResponse, 400: dict})
async def register_user(request: HttpRequest, payload: RegisterRequest) -> HttpResponse:
    if not services.CaptchaService.verify_turnstile(payload.turnstile_token):
        return 400, {
            "error": "The robot was not checked. Try again",
            "i18n": "captcha_verification_failed",
        }

    email = payload.email
    user = await User.objects.filter(email=email).afirst()

    if user:
        if user.is_active:
            return 400, {
                "error": "The user with this email already exists",
                "i18n": "email_already_exists",
            }

        user.set_password(payload.password)
        await user.asave()
    else:
        user = await sync_to_async(User.objects.create_user)(
            email=email, password=payload.password, is_active=False
        )

    otp_sent = await services.OTPAuthService.generate_and_send_otp(email)

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
async def login_user(request: HttpRequest, payload: LoginRequest) -> HttpResponse:
    user = await aauthenticate(
        request, username=payload.email, password=payload.password
    )

    if user is None:
        return 400, {
            "error": "Invalid email or password.",
            "i18n": "invalid_email_or_password",
        }

    if not user.is_active:
        await services.OTPAuthService.generate_and_send_otp(user.email)
        return 400, {
            "error": "Your account has not been activated. We have sent a new OTP code to your email.",
            "i18n": "account_not_activated",
        }

    await alogin(request, user)

    return 200, {
        "success": True,
        "message": "Authorization is successful.",
        "i18n": "authorization_successful",
    }


@router.post(
    "/delete/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def delete_user(request: HttpRequest, payload: DeleteUserRequest) -> HttpResponse:
    try:
        success = await services.delete_user(request.user, payload.password)
    except Exception as e:
        logger.error(f"Delete user is failde: {str(e)}", exc_info=True)
        return 400, {
            "message": "Delete user is failde",
            "i18n": "delete_user_failed",
        }
    else:
        if not success:
            return 400, {
                "message": "Password is incorrect",
                "i18n": "delete_user_password_incorrect",
            }
    return 200, {
        "success": True,
        "message": "Delete user is seccusse",
        "i18n": "delete_user_seccusse",
    }


@router.post(
    "/password/change/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def change_password(
    request: HttpRequest, payload: ChangePasswordRequest
) -> HttpResponse:
    try:
        success = await services.PasswordService.change_password(
            user=request.user,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
    except Exception as e:
        logger.error(f"Change password failed: {str(e)}", exc_info=True)
        return 400, {
            "message": "Change password failed",
            "i18n": "change_password_failed",
        }
    else:
        if not success:
            return 400, {
                "message": "Old password is incorrect",
                "i18n": "old_password_incorrect",
            }

    return 200, {
        "success": True,
        "message": "Password successfully changed",
        "i18n": "password_changed_successfully",
    }


@router.post("/password/forgot/", response={200: SuccessResponse, 400: dict})
async def forgot_password(
    request: HttpRequest, payload: ForgotPasswordRequest
) -> HttpResponse:
    if not services.CaptchaService.verify_turnstile(payload.turnstile_token):
        return 400, {
            "error": "The robot was not checked. Try again",
            "i18n": "captcha_verification_failed",
        }

    await services.PasswordService.generate_reset_otp(payload.email)

    return 200, {
        "success": True,
        "message": "If this email is registered, a recovery code has been sent.",
        "i18n": "recovery_code_sent",
    }


@router.post("/password/reset/", response={200: SuccessResponse, 400: dict})
async def reset_password(
    request: HttpRequest, payload: ResetPasswordRequest
) -> HttpResponse:
    success = await services.PasswordService.verify_reset_and_save(
        email=payload.email, code=payload.code, new_password=payload.new_password
    )

    if not success:
        return 400, {
            "error": "Invalid or outdated code, or user not found.",
            "i18n": "invalid_reset_code",
        }

    return 200, {
        "success": True,
        "message": "Password successfully reset.",
        "i18n": "password_reset_successfully",
    }


@router.post(
    "/blacklist/companies/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def edit_companies_blacklist(
    request: HttpRequest, payload: CompanyBlacklistRequest
) -> HttpResponse:
    try:
        message = await services.edit_blacklist(
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
    "/add-viewed-vacancy/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def add_viewed_vacancy(
    request: HttpRequest, payload: AddViewedVacancy
) -> HttpResponse:
    try:
        success = await services.update_viewed_vacancies(
            user=request.user, vacancy_id=payload.vacancy
        )
    except Exception as e:
        logger.error(f"Update viewed vacancies is failde: {str(e)}", exc_info=True)
        return 400, {"message": "Update viewed vacancies is failde"}
    else:
        if not success:
            return 400, {"message": "Vacancy or User not found"}
    return 200, {"success": True, "message": "The vacancy is marked as viewed"}


@router.post(
    "/notification/read/",
    auth=django_auth,
    response={200: SuccessResponse, 404: dict},
)
def read_notification(
    request: HttpRequest, payload: ReadNotificationRequest
) -> HttpResponse:
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
