import logging

from django.http import HttpRequest
from ninja import Router
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.cooperation import services

from .schemas import CreateMessageRequest, SuccessResponse

logger = logging.getLogger(__name__)

router = Router(
    tags=["Cooperation API"],
    throttle=[AnonRateThrottle("3/m"), AuthRateThrottle("3/m")],
)


@router.post(
    "/cooperation/create/message/",
    response={200: SuccessResponse},
    throttle=[AnonRateThrottle("3/m"), AuthRateThrottle("3/m")],
)
async def create_message(request: HttpRequest, payload: CreateMessageRequest):
    try:
        await services.process_cooperation_offer(payload)

        logger.info(f"New offer from: {payload.name} ({payload.email})")

        return 200, SuccessResponse(success=True, i18n="cooperation.success_desc")
    except Exception as e:
        logger.error(f"Save offer is failed: {str(e)}", exc_info=True)
