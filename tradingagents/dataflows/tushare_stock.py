from datetime import datetime
from typing import Annotated

from .tushare_common import get_pro_api, resolve_tushare_code, format_date, handle_tushare_error


def get_stock(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get daily OHLCV stock data from Tushare.

    Args:
        symbol: Ticker symbol (e.g. '000001', '600000', or '000001.SZ')
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        CSV string containing daily OHLCV data
    """
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    ts_code = resolve_tushare_code(symbol)
    ts_start = format_date(start_date)
    ts_end = format_date(end_date)

    try:
        pro = get_pro_api()
        df = pro.daily(
            ts_code=ts_code,
            start_date=ts_start,
            end_date=ts_end,
        )
    except Exception as e:
        handle_tushare_error(e, f"daily({ts_code})")

    if df is None or df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    # Rename columns to match yfinance output format
    col_map = {
        "trade_date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "vol": "Volume",
        "amount": "Amount",
    }
    df = df.rename(columns=col_map)

    # Sort by date ascending
    if "Date" in df.columns:
        df["Date"] = df["Date"].apply(lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}")
        df = df.sort_values("Date").reset_index(drop=True)

    # Round price columns
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df[col] = df[col].round(2)

    csv_string = df.to_csv(index=False)

    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(df)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
