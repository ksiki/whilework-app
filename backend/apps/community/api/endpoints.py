import logging
import uuid

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import Query, Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from apps.community import services

from .schemas import (
    CreateSuggestRequest,
    GetPoductionsLogsRequest,
    GetSuggestsRequest,
    SuccessResponse,
)

logger = logging.getLogger(__name__)

router = Router(tags=["Cooperation API"])


@router.get("/production_logs/", include_in_schema=False)
def get_production_logs(
    request: HttpRequest, query: Query[GetPoductionsLogsRequest]
) -> HttpResponse:
    logs = services.get_production_logs(page_num=query.page)
    if logs is None:
        return HttpResponse("")

    context = {
        "logs": logs,
    }
    return render(request, "community/includes/_production_log.html", context)


@router.get("/suggests/", include_in_schema=False)
def get_suggests(
    request: HttpRequest, query: Query[GetSuggestsRequest]
) -> HttpResponse:
    suggests = services.get_suggests(page_num=query.page, order_by=query.sort)
    if suggests is None:
        return HttpResponse("")

    liked_suggest_ids = services.get_liked_suggest_ids(request.user, suggests)

    context = {
        "suggests": suggests,
        "liked_suggest_ids": liked_suggest_ids,
    }
    return render(request, "community/includes/_suggest.html", context)


@router.post(
    "/suggest/{suggest_id}/like/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
)
async def like_suggest(request: HttpRequest, suggest_id: uuid.UUID):
    try:
        success = await services.like_suggest(
            suggest_id=suggest_id, user_id=request.user.id
        )
    except Exception as e:
        logger.error(f"Like the suggest failed: {str(e)}", exc_info=True)
        return 400, {"message": "Like the suggest failed"}
    else:
        if not success:
            return 400, {"message": "Suggest or User not found"}

    return 200, {"success": True, "message": "Success"}


@router.post(
    "/suggest/create/",
    auth=django_auth,
    response={200: SuccessResponse, 400: dict},
    throttle=[AnonRateThrottle("15/m"), AuthRateThrottle("15/m")],
)
async def create_suggest(
    request: HttpRequest, payload: CreateSuggestRequest
) -> HttpResponse:
    try:
        success = await services.create_suggest(
            user_id=request.user.id, payload=payload
        )
    except Exception as e:
        logger.error(f"Create suggest failed: {str(e)}", exc_info=True)
        return 400, {"message": "Create suggest failed"}
    else:
        if not success:
            return 400, {"message": "Invalid payload or User not found"}

    return 200, {"success": True, "message": "Success"}
