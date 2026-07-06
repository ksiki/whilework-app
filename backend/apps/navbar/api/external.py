import logging

from django.http import HttpRequest, HttpResponse
from ninja import Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.navbar import services

from .schemas import CreateSupportMessageRequest, SuccessResponse

logger = logging.getLogger(__name__)

router = Router(tags=["Navbar API"])


@router.post(
    "/create/support-message/",
    auth=django_auth,
    response={200: SuccessResponse},
    throttle=[AnonRateThrottle("15/m"), AuthRateThrottle("15/m")],
)
async def create_support_message(
    request: HttpRequest, payload: CreateSupportMessageRequest
) -> HttpResponse:
    try:
        success = await services.create_support_message(
            user_id=request.user.id, payload=payload
        )
        logger.info(f"Support message from user: {request.user.id})")
    except Exception as e:
        logger.error(f"Save support message is failed: {str(e)}", exc_info=True)
        return 400, {"message": "Save support message is failed"}
    else:
        if not success:
            return 400, {"message": "User not found"}
    return 200, {"success": True}
