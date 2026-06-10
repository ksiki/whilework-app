import logging

from django.http import HttpRequest
from ninja import Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.vacancies import services

from .schemas import ComplaintRequest, SuccessResponse

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
async def create_complaint(request: HttpRequest, payload: ComplaintRequest):
    success = await services.add_complaint(user_id=request.user.id, payload=payload)

    if not success:
        return 400, {"message": "Vacancy not found"}
    return 200, {"success": True}
