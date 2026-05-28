import uuid

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.sources import services
from apps.sources.models import Source, SourceTopic

from .serializers import SourceSerializer


class SourceAPIViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/internal/v1/sources/
    POST /api/internal/v1/sources/<uuid:source_id>/report-error/
    """

    serializer_class = SourceSerializer

    def get_queryset(self):
        return services.get_active_sources()

    @action(detail=True, methods=["post"], url_path="report-error")
    def report_error(self, request: Request, pk: uuid.UUID) -> Response:
        error_message = request.data.get("error_message", "Unknown error")
        topic_uuid_str = request.data.get("topic_id")

        try:
            if topic_uuid_str:
                topic_uuid = uuid.UUID(topic_uuid_str)
                services.register_parsing_error(
                    target_id=topic_uuid, error_message=error_message, is_topic=True
                )
            else:
                services.register_parsing_error(
                    target_id=pk, error_message=error_message, is_topic=False
                )
            return Response({"detail": "Error reported"}, status=status.HTTP_200_OK)
        except (Source.DoesNotExist, SourceTopic.DoesNotExist):
            return Response(
                {"error": "Target not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid UUID format in payload"},
                status=status.HTTP_400_BAD_REQUEST,
            )
