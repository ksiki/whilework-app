import logging

from django.http import HttpRequest, HttpResponse
from ninja import Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.vacancies import services

from .schemas import ComplaintRequest, ShowContactsRequest, SuccessResponse

router = Router(
    tags=["Vacancies Api"],
    throttle=[AnonRateThrottle("15/m"), AuthRateThrottle("15/m")],
)
logger = logging.getLogger(__name__)


@router.post(
    "/complaint/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def create_complaint(
    request: HttpRequest, payload: ComplaintRequest
) -> HttpResponse:
    try:
        success = await services.add_complaint(user_id=request.user.id, payload=payload)
        logger.info(f"Complaint from user: {request.user.id})")
    except Exception as e:
        logger.error(f"Save complaint is failed: {str(e)}", exc_info=True)
        return 400, {"message": "Save complaint is failed"}
    else:
        if not success:
            return 400, {"message": "Vacancy not found"}
    return 200, {"success": True}


@router.post(
    "/show-contacts/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def update_show_contacts_views(
    request: HttpRequest, payload: ShowContactsRequest
) -> HttpResponse:
    try:
        success = await services.update_contacts_views(vacancy_id=payload.vacancy)
    except Exception as e:
        logger.error(f"Update contacts views is failde: {str(e)}", exc_info=True)
        return 400, {"message": "Update contacts views is failde"}
    else:
        if not success:
            return 400, {"message": "Vacancy not found"}
    return 200, {"success": True}
