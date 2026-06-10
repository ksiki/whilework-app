import uuid

from ninja import Schema

from apps.vacancies.models import Complaint


class SuccessResponse(Schema):
    success: bool


class ComplaintRequest(Schema):
    vacancy: uuid.UUID
    reason: Complaint.Reason
    details: str | None = None
