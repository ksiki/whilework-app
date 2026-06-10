from ninja import Schema


class ReportRequest(Schema):
    url: str


class SuccessResponse(Schema):
    success: bool
