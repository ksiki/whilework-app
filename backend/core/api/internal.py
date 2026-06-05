from apps.inbox.endpoints import router as inbox_router
from apps.sources.endpoints import router as sources_router
from ninja import NinjaAPI

internal_api = NinjaAPI(
    title="Internal API",
    version="v1",
    description="API for internal microservices communication",
)

internal_api.add_router("/inbox/", inbox_router)
internal_api.add_router("/sources/", sources_router)
internal_api.add_exception_handler
