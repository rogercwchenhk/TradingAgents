from datetime import datetime
from typing import Annotated

from .tushare_common import get_pro_api, resolve_tushare_code, format_date, handle_tushare_error


def get_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get news for a specific stock from Tushare.

    Uses the news API to fetch company-specific news articles.
    """
    ts_code = resolve_tushare_code(ticker)
    ts_start = format_date(start_date)
    ts_end = format_date(end_date)

    try:
        pro = get_pro_api()
        df = pro.news(
            src="sina",
            start_date=ts_start,
            end_date=ts_end,
        )
    except Exception as e:
        handle_tushare_error(e, f"news({ts_code})")

    if df is None or df.empty:
        return f"No news found for {ticker} between {start_date} and {end_date}"

    # Filter by ts_code if the news API returns all stocks
    if "ts_code" in df.columns:
        ticker_news = df[df["ts_code"] == ts_code]
        if not ticker_news.empty:
            df = ticker_news

    news_str = ""
    for _, row in df.iterrows():
        title = row.get("title", "No title")
        content = row.get("content", "")
        pub_date = row.get("pub_date", "")
        src = row.get("src", "Unknown")

        news_str += f"### {title} (source: {src})\n"
        if pub_date:
            news_str += f"Date: {pub_date}\n"
        if content:
            news_str += f"{content}\n"
        news_str += "\n"

    if not news_str:
        return f"No news found for {ticker} between {start_date} and {end_date}"

    return f"## {ticker} News, from {start_date} to {end_date}:\n\n{news_str}"


def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: int = 7,
    limit: int = 10,
) -> str:
    """Get global/macro economic news from Tushare.

    Uses the news API with macro-economic source to fetch global market news.
    """
    from dateutil.relativedelta import relativedelta

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - relativedelta(days=look_back_days)
    ts_start = format_date(start_dt.strftime("%Y-%m-%d"))
    ts_end = format_date(curr_date)

    try:
        pro = get_pro_api()
        # Fetch macro-economic news
        df = pro.news(
            src="sina",
            start_date=ts_start,
            end_date=ts_end,
        )
    except Exception as e:
        handle_tushare_error(e, "global_news")

    if df is None or df.empty:
        return f"No global news found for {curr_date}"

    # Filter for macro/economy related keywords
    macro_keywords = ["经济", "市场", "股市", "央行", "利率", "通胀", "GDP", "政策",
                      "economy", "market", "fed", "interest", "inflation", "policy",
                      "trade", "global", "recession", "growth"]

    if "title" in df.columns:
        mask = df["title"].str.contains("|".join(macro_keywords), case=False, na=False)
        if "content" in df.columns:
            mask = mask | df["content"].str.contains("|".join(macro_keywords), case=False, na=False)
        macro_news = df[mask]
        if not macro_news.empty:
            df = macro_news

    # Apply limit
    df = df.head(limit)

    start_date = start_dt.strftime("%Y-%m-%d")
    news_str = ""
    for _, row in df.iterrows():
        title = row.get("title", "No title")
        content = row.get("content", "")
        pub_date = row.get("pub_date", "")
        src = row.get("src", "Unknown")

        news_str += f"### {title} (source: {src})\n"
        if pub_date:
            news_str += f"Date: {pub_date}\n"
        if content:
            news_str += f"{content}\n"
        news_str += "\n"

    if not news_str:
        return f"No global news found for {curr_date}"

    return f"## Global Market News, from {start_date} to {curr_date}:\n\n{news_str}"


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol of the company"],
) -> str:
    """Get insider/manager transactions data from Tushare.

    Uses stk_manager_interface to fetch insider trading data.
    """
    ts_code = resolve_tushare_code(ticker)

    try:
        pro = get_pro_api()
        df = pro.stk_manager_interface(ts_code=ts_code)
    except Exception as e:
        handle_tushare_error(e, f"stk_manager_interface({ts_code})")

    if df is None or df.empty:
        return f"No insider transactions data found for symbol '{ticker}'"

    csv_string = df.to_csv(index=False)

    header = f"# Insider Transactions data for {ticker.upper()}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
