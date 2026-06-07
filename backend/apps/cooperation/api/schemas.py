from ninja import Schema
from pydantic import EmailStr, Field


class CreateMessageRequest(Schema):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=50, max_length=3000)


class SuccessResponse(Schema):
    success: bool
    i18n: str
