from apps.inbox.api.internal import router as inbox_router
from apps.sources.api.internal import router as sources_router
from ninja import NinjaAPI

api = NinjaAPI(
    title="Internal API",
    urls_namespace="internal-api-v1",
    version="v1",
    description="API for internal microservices communication",
)

api.add_router("/inbox/", inbox_router)
api.add_router("/sources/", sources_router)
api.add_exception_handler
