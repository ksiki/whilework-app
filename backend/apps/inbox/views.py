from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import atomic_saved_messages_and_update_sources


class ReceiveRawBatchView(APIView):
    """POST /api/internal/v1/inbox/batch/"""

    def post(self, request: HttpRequest) -> Response:
        messages_data = request.data.get("messages", [])

        if not messages_data:
            return Response(
                {"error": "Empty batch"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            atomic_saved_messages_and_update_sources(messages_data=messages_data)
            return Response(
                {"detail": "Processed messages successfully."},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"Database error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
