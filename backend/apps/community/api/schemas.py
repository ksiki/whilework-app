from ninja import Schema


class SuccessResponse(Schema):
    success: bool


class CreateSuggestRequest(Schema):
    title: str
    description: str


class GetPoductionsLogsRequest(Schema):
    page: int


class GetSuggestsRequest(Schema):
    page: int
    sort: str
