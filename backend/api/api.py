from fastapi import APIRouter

from .endpoints import auth, processing, admin_ui, crawl

api_router = APIRouter()

api_router.include_router(crawl.router, tags=["crawl"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(processing.router, prefix="/v1", tags=["processing"])
api_router.include_router(admin_ui.router) # No prefix for admin UI
