from typing import Any, Dict, List

from ninja import Field, Schema


class BatchRequestSchema(Schema):
    messages: List[Dict[str, Any]] = Field(..., description="Raw messages list")


class SuccessResponseSchema(Schema):
    detail: str


class ErrorResponseSchema(Schema):
    error: str
