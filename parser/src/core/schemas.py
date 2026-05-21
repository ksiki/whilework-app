from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class RawMessageCreate(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)

    source_id: int = Field(..., description="Source ID in the Django database")
    external_msg_id: str = Field(
        ...,
        max_length=255,
        description="The message ID inside the target platform",
    )
    raw_text: str = Field(
        ...,
        min_length=1,
        description="The original text of the message remains unchanged",
    )
    metadata: Dict[str, Any] = Field(
        ...,
        default_factory=dict,
        description="For example: date, author",
    )


class RawMessageBatch(BaseModel):
    """
    DTO for batch sending RawMessage
    """

    model_config = ConfigDict(frozen=True, strict=True)

    messages: list[RawMessageCreate] = Field(
        ...,
        max_length=100,
    )
