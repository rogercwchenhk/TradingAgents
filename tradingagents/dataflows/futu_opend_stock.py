from datetime import datetime
from typing import Annotated

import pandas as pd
from futu import KLType, AuType, RET_ERROR

from .futu_opend_common import _get_quote_context, resolve_futu_code, FutuRateLimitError


def get_stock(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    futu_code = resolve_futu_code(symbol)
    ctx = _get_quote_context()

    ret, data, _ = ctx.request_history_kline(
        futu_code,
        start=start_date,
        end=end_date,
        ktype=KLType.K_DAY,
        autype=AuType.QFQ,
    )

    if ret == RET_ERROR:
        msg = str(data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving stock data for {symbol}: {msg}"

    if data is None or data.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    df = data.rename(columns={
        "time_key": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "turnover": "Turnover",
    })

    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    numeric_columns = ["Open", "High", "Low", "Close"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].round(2)

    output_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume", "Turnover"] if c in df.columns]
    csv_string = df[output_cols].to_csv(index=False)

    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Futu code: {futu_code}\n"
    header += f"# Total records: {len(df)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
