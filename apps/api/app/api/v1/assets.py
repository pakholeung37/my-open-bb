from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.repositories.market_repository import MarketRepository
from app.schemas import AssetOverviewOut

router = APIRouter(tags=["assets"])


@router.get("/assets/{symbol}", response_model=AssetOverviewOut)
def asset_overview(symbol: str) -> AssetOverviewOut:
    settings = get_settings()
    repository = MarketRepository(settings.database_path)
    row = repository.get_asset_overview(symbol)
    if not row:
        raise HTTPException(status_code=404, detail=f"Asset {symbol.upper()} not found")
    return AssetOverviewOut(**row)
