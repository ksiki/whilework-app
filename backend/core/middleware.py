import secrets
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

from core import settings


class InternalSystemAuthMiddleware:
    """
    Middleware to protect the aggregator's internal endpoints.
    Checks the presence and validity of the X-Internal-Secret header.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startwith("/api/internal/"):
            provided_secret = request.headers.get("X-Internal-Secret")
            expected_secret = getattr(settings, "INTERNAL_API_SECRET", None)

            if (
                not provided_secret
                or not expected_secret
                or not secrets.compare_digest(provided_secret, expected_secret)
            ):
                return JsonResponse(
                    {"error": "Forbidden. Invalid or missing internal token"},
                    status=403,
                )

        return self.get_response(request)
