from datetime import datetime, timedelta
from typing import Annotated

from futu import RET_ERROR

from .futu_opend_common import _get_quote_context, resolve_futu_code, FutuRateLimitError


def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    futu_code = resolve_futu_code(ticker)
    ctx = _get_quote_context()

    ret, news_data = ctx.get_news_list(futu_code)
    if ret == RET_ERROR:
        msg = str(news_data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving news for {ticker}: {msg}"

    if news_data is None or news_data.empty:
        return f"No news found for {ticker}"

    news_data["datetime"] = news_data["time"].apply(lambda x: str(x)[:10] if x else "")

    filtered = news_data[
        (news_data["datetime"] >= start_date) &
        (news_data["datetime"] <= end_date)
    ]

    if filtered.empty:
        return f"No news found for {ticker} between {start_date} and {end_date}"

    news_str = ""
    for _, row in filtered.iterrows():
        title = row.get("title", "No title")
        source = row.get("source", "Unknown")
        content = row.get("content", "")
        news_str += f"### {title} (source: {source})\n"
        if content:
            news_str += f"{content}\n"
        news_str += "\n"

    return f"## {ticker} News, from {start_date} to {end_date}:\n\n{news_str}"


def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    ctx = _get_quote_context()

    ret, news_data = ctx.get_global_news()
    if ret == RET_ERROR:
        msg = str(news_data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving global news: {msg}"

    if news_data is None or news_data.empty:
        return f"No global news found for {curr_date}"

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    news_data["datetime"] = news_data["time"].apply(lambda x: str(x)[:10] if x else "")
    filtered = news_data[
        (news_data["datetime"] >= start_date) &
        (news_data["datetime"] <= curr_date)
    ]

    if filtered.empty:
        return f"No global news found between {start_date} and {curr_date}"

    news_str = ""
    count = 0
    for _, row in filtered.iterrows():
        if count >= limit:
            break
        title = row.get("title", "No title")
        source = row.get("source", "Unknown")
        content = row.get("content", "")
        news_str += f"### {title} (source: {source})\n"
        if content:
            news_str += f"{content}\n"
        news_str += "\n"
        count += 1

    return f"## Global Market News, from {start_date} to {curr_date}:\n\n{news_str}"


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    futu_code = resolve_futu_code(ticker)
    ctx = _get_quote_context()

    ret, data = ctx.get_capital_flow(futu_code)
    if ret == RET_ERROR:
        msg = str(data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving capital flow for {ticker}: {msg}"

    if data is None or data.empty:
        return f"No capital flow / insider transactions data found for symbol '{ticker}'"

    csv_string = data.to_csv()
    header = f"# Capital Flow / Insider Transactions data for {ticker.upper()}\n"
    header += f"# Futu code: {futu_code}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
