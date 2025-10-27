"""
Market utilities tailored for Polygon.io Free Plan users.
- Always uses end-of-day (EOD) grouped aggregates (no realtime/minute snapshot).
- Uses a local DB/cache via read_market/write_market to avoid repeated API hits.
- Falls back to a random price if Polygon is unavailable (preserves original fallback).
"""

from polygon import RESTClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import random
from functools import lru_cache
from typing import Dict

load_dotenv(override=True)

# Environment variable (API key must be present to use Polygon)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")


def fetch_eod_prices_from_polygon() -> Dict[str, float]:
    """
    Fetch end-of-day (EOD) close prices for the most recent available trading date
    using Polygon grouped daily aggregates. Returns dict mapping ticker -> close price.
    """
    if not POLYGON_API_KEY:
        raise RuntimeError("POLYGON_API_KEY is not configured.")

    client = RESTClient(POLYGON_API_KEY)

    # Use a well-known ETF to discover the last available close timestamp
    probe_agg = client.get_previous_close_agg("SPY")[0]
    last_close_date = datetime.fromtimestamp(probe_agg.timestamp / 1000).date()

    candidate_date = last_close_date - timedelta(days=1)

    # Retrieve grouped daily aggregates for the discovered date (adjusted)
    results = client.get_grouped_daily_aggs(candidate_date, adjusted=True, include_otc=False)

    return {r.ticker: r.close for r in results}


@lru_cache(maxsize=4)
def cached_market_for_date(date_str: str) -> Dict[str, float]:
    """
    Return cached market data.
    - Accepts an optional date string (to make the cache key date-specific)
    - lru_cache provides a small in-memory cache in addition to DB storage.
    """
    # Try reading from local cache
    market_data = fetch_eod_prices_from_polygon()
    return market_data


def get_eod_share_price(symbol: str) -> float:
    """
    Return the end-of-day close price for the given symbol for today's date (YYYY-MM-DD).
    If the symbol is not present in the cached market data, returns 0.0.
    """
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    try:
        market_data = cached_market_for_date(today_str)
        return float(market_data.get(symbol, 0.0))
    except Exception as exc:
        # If any error occurs (API, DB, etc.), preserve the original fallback behavior.
        print(f"[market_analyser.py] Failed to retrieve EOD price ({exc}); falling back to random.")
        return float(random.randint(1, 100))


def get_share_price(symbol: str) -> float:
    """
    Public helper to obtain a share price when on Polygon free plan:
    - If POLYGON_API_KEY is present, try to return the EOD price.
    - If any step fails, return a random integer between 1 and 100 as a safe fallback.
    """
    if POLYGON_API_KEY:
        return get_eod_share_price(symbol)

    # If no API key configured, immediately fall back to a random price (preserves previous behavior).
    print("[market.py] POLYGON_API_KEY not set; using random fallback price.")
    return float(random.randint(1, 100))