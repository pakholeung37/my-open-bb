from fastapi import APIRouter

from app.core.config import get_settings
from app.repositories.market_repository import MarketRepository
from app.schemas import WatchlistQuoteOut
from app.services.config_service import load_watchlist

router = APIRouter(tags=["market"])


@router.get("/market/watchlist", response_model=list[WatchlistQuoteOut])
def watchlist_quotes():
    settings = get_settings()
    watchlist = load_watchlist(settings.watchlist_path)
    repository = MarketRepository(settings.database_path)
    rows = repository.list_watchlist_quotes(watchlist)
    return [WatchlistQuoteOut(**row) for row in rows]
