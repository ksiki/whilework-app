import uuid

from ninja import Schema
from pydantic import EmailStr, Field


class RegisterRequest(Schema):
    email: EmailStr
    password: str = Field(..., min_length=8)


class VerifyOTPRequest(Schema):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4, description="4-digit OTP code")


class SuccessResponse(Schema):
    success: bool
    message: str
    i18n: str = ""


class LoginRequest(Schema):
    email: EmailStr
    password: str


class CompanyBlacklistRequest(Schema):
    company_id: uuid.UUID
    delete: bool


class AddViewedVacancy(Schema):
    vacancy: uuid.UUID


class ReadNotificationRequest(Schema):
    notification_id: uuid.UUID
