import uuid
from typing import List, Optional

from ninja import ModelSchema, Schema

from apps.sources.models import Source, SourceTopic


class SourceTopicSchema(ModelSchema):
    class Meta:
        model = SourceTopic
        fields = ["id", "topic_id", "last_parsed_id"]


class SourceSchema(ModelSchema):
    platform: str
    topics: List[SourceTopicSchema]

    class Meta:
        model = Source
        fields = ["id", "identifier", "last_parsed_id"]

    @staticmethod
    def resolve_platform(obj: Source) -> str:
        return obj.get_platform_display()

    @staticmethod
    def resolve_topics(obj: Source):
        return obj.active_topics


class ReportErrorInSchema(Schema):
    error_message: str = "Unknown error"
    topic_id: Optional[uuid.UUID] = None


class MessageResponseSchema(Schema):
    detail: str


class ErrorResponseSchema(Schema):
    error: str
