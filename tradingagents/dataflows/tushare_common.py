import os
import logging

logger = logging.getLogger(__name__)


class TushareRateLimitError(Exception):
    """Exception raised when Tushare API rate limit or access limit is exceeded."""
    pass


_pro_api = None


def get_api_token() -> str:
    """Retrieve the Tushare API token from environment variables."""
    token = os.getenv("TUSHARE_API_KEY")
    if not token:
        raise ValueError("TUSHARE_API_KEY environment variable is not set.")
    return token


def get_pro_api():
    """Get or create a lazy singleton Tushare Pro API client."""
    global _pro_api
    if _pro_api is None:
        import tushare as ts
        token = get_api_token()
        ts.set_token(token)
        _pro_api = ts.pro_api()
    return _pro_api


def resolve_tushare_code(symbol: str) -> str:
    """Convert a plain ticker symbol to Tushare's ts_code format.

    Tushare uses the format: {code}.{exchange}
    - 6-digit codes starting with 6 -> SH (Shanghai)
    - 6-digit codes starting with 0/3 -> SZ (Shenzhen)
    - Symbols already containing '.' are returned as-is.
    - US/HK symbols are converted to uppercase and returned with .SI suffix
      (Tushare supports some overseas stocks via .SI).
    """
    symbol = symbol.strip().upper()

    # Already in ts_code format
    if '.' in symbol:
        return symbol

    # Pure numeric -> Chinese A-share
    if symbol.isdigit():
        if len(symbol) != 6:
            # Pad shorter codes
            symbol = symbol.zfill(6)
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"

    # Non-numeric (e.g. AAPL, 0700.HK) -> treat as overseas
    # Tushare overseas suffix is .SI for Singapore-listed, but most
    # international tickers aren't well supported. Return as-is and
    # let the API decide.
    return symbol


def format_date(date_str: str) -> str:
    """Convert yyyy-mm-dd date to Tushare's YYYYMMDD format."""
    return date_str.replace("-", "")


def handle_tushare_error(e: Exception, context: str = ""):
    """Check if a Tushare error is rate-limit related and raise TushareRateLimitError."""
    err_msg = str(e).lower()
    if "exceed" in err_msg or "limit" in err_msg or "freq" in err_msg or "每分钟" in err_msg:
        raise TushareRateLimitError(f"Tushare rate limit exceeded{': ' + context if context else ''}: {e}")
    raise
