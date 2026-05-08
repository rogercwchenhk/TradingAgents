from datetime import datetime
from typing import Annotated

from futu import RET_ERROR

from .futu_opend_common import _get_quote_context, resolve_futu_code, FutuRateLimitError


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date (not used for Futu)"] = None,
) -> str:
    futu_code = resolve_futu_code(ticker)
    ctx = _get_quote_context()

    ret, data = ctx.get_stock_basicinfo_list(
        market=futu_code.split(".")[0],
        stock_type=[],
        code_list=[futu_code],
    )

    if ret == RET_ERROR:
        msg = str(data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving fundamentals for {ticker}: {msg}"

    if data is None or data.empty:
        return f"No fundamentals data found for symbol '{ticker}'"

    lines = []
    for col in data.columns:
        val = data.iloc[0][col]
        if val is not None and str(val).strip():
            lines.append(f"{col}: {val}")

    ret2, quote_data = ctx.get_market_snapshot([futu_code])
    if ret2 == 0 and quote_data is not None and not quote_data.empty:
        row = quote_data.iloc[0]
        snapshot_fields = [
            ("Last Price", "last_price"),
            ("Open", "open_price"),
            ("High", "high_price"),
            ("Low", "low_price"),
            ("Prev Close", "prev_close_price"),
            ("Volume", "volume"),
            ("Turnover", "turnover"),
            ("PE Ratio (TTM)", "pe_ttm_ratio"),
            ("PB Ratio", "pb_ratio"),
            ("Dividend Yield", "dividend_yield"),
            ("Market Cap", "market_val"),
        ]
        for label, col_name in snapshot_fields:
            if col_name in row.index:
                val = row[col_name]
                if val is not None and str(val).strip() and str(val) != "nan":
                    lines.append(f"{label}: {val}")

    header = f"# Company Fundamentals for {ticker.upper()}\n"
    header += f"# Futu code: {futu_code}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + "\n".join(lines)


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    return _get_financial_report(ticker, "balance_sheet", freq, curr_date)


def get_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    return _get_financial_report(ticker, "cashflow", freq, curr_date)


def get_income_statement(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    return _get_financial_report(ticker, "income", freq, curr_date)


def _get_financial_report(ticker: str, report_type: str, freq: str, curr_date: str) -> str:
    futu_code = resolve_futu_code(ticker)
    ctx = _get_quote_context()

    from futu import FinancialReportType
    report_map = {
        "balance_sheet": FinancialReportType.REPORT_BALANCE_SHEET,
        "cashflow": FinancialReportType.REPORT_CASHFLOW,
        "income": FinancialReportType.REPORT_INCOME,
    }

    futu_report_type = report_map.get(report_type)
    if futu_report_type is None:
        return f"Unsupported report type: {report_type}"

    ret, report_data = ctx.get_finance_summary([futu_code], futu_report_type)
    if ret == RET_ERROR:
        msg = str(report_data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving {report_type} for {ticker}: {msg}"

    if report_data is None or report_data.empty:
        return f"No {report_type} data found for symbol '{ticker}'"

    csv_string = report_data.to_csv()
    header = f"# {report_type.replace('_', ' ').title()} data for {ticker.upper()} ({freq})\n"
    header += f"# Futu code: {futu_code}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
