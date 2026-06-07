import secrets
from typing import Callable

from django.core.cache import cache
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
        if request.path.startswith("/api/internal/"):
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


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        self.limit = 60
        self.window = 60

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            identifier = f"ip_{request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR'))}"

        cache_key = f"ratelimit:{identifier}"

        try:
            requests = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=self.window)
            requests = 1

        if requests > self.limit:
            return JsonResponse(
                {
                    "error": "Too Many Requests",
                    "detail": f"Limit of {self.limit} requests per {self.window}s exceeded.",
                },
                status=429,
            )

        return self.get_response(request)
