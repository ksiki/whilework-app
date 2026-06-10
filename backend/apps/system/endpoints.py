import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from ninja import Router
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from .models import Report404
from .schemas import ReportRequest, SuccessResponse

logger = logging.getLogger(__name__)

router = Router(
    tags=["System API"],
    throttle=[AnonRateThrottle("3/m"), AuthRateThrottle("3/m")],
)


@router.post("/report-404/", response={200: SuccessResponse})
async def report_404(request: HttpRequest, report: ReportRequest) -> HttpResponse:
    await Report404.objects.acreate(url=report.url)
    return 200, {
        "success": True,
    }


def global_404_handler(request: HttpRequest, exception) -> HttpResponse:
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Not Found"}, status=404)

    return render(request, "errors/404.html", status=404)
