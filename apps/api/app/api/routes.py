from fastapi import APIRouter

from app.api.v1 import assets, feed, health, market, refresh

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(feed.router)
api_router.include_router(market.router)
api_router.include_router(assets.router)
api_router.include_router(refresh.router)
