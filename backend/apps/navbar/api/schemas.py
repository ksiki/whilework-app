from ninja import Schema


class SuccessResponse(Schema):
    success: bool


class CreateSupportMessageRequest(Schema):
    title: str
    message: str
