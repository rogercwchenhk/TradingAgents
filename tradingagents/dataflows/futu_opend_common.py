import os
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_quote_ctx: Optional[object] = None


def _get_quote_context():
    global _quote_ctx
    if _quote_ctx is not None:
        return _quote_ctx

    from futu import OpenQuoteContext
    from .config import get_config

    config = get_config()
    host = config.get("futu_opend_host", "127.0.0.1")
    port = config.get("futu_opend_port", 11111)

    _quote_ctx = OpenQuoteContext(host=host, port=port)
    return _quote_ctx


def close_quote_context():
    global _quote_ctx
    if _quote_ctx is not None:
        try:
            _quote_ctx.close()
        except Exception:
            pass
        _quote_ctx = None


def resolve_futu_code(symbol: str) -> str:
    from .config import get_config

    config = get_config()
    market = config.get("futu_market", "US").upper()

    symbol = symbol.strip().upper()

    if symbol.startswith("US.") or symbol.startswith("HK."):
        return symbol

    if market == "HK":
        padded = symbol.zfill(5)
        return f"HK.{padded}"
    else:
        return f"US.{symbol}"


class FutuRateLimitError(Exception):
    pass
