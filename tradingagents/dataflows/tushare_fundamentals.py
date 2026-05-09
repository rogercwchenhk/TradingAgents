from datetime import datetime
from typing import Annotated

from .tushare_common import get_pro_api, resolve_tushare_code, format_date, handle_tushare_error


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get company fundamentals overview from Tushare.

    Uses daily_basic for valuation metrics and stock_basic for company info.
    """
    ts_code = resolve_tushare_code(ticker)

    try:
        pro = get_pro_api()

        # Get company basic info
        basic_info = pro.stock_basic(ts_code=ts_code, fields="ts_code,name,industry,market,list_date")

        # Get daily basic metrics (PE, PB, etc.)
        daily_params = {"ts_code": ts_code, "fields": "ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,ps,total_mv,circ_mv"}
        if curr_date:
            daily_params["end_date"] = format_date(curr_date)
        daily_basic = pro.daily_basic(**daily_params)

    except Exception as e:
        handle_tushare_error(e, f"fundamentals({ts_code})")

    lines = []

    if basic_info is not None and not basic_info.empty:
        row = basic_info.iloc[0]
        lines.append(f"Name: {row.get('name', 'N/A')}")
        lines.append(f"Industry: {row.get('industry', 'N/A')}")
        lines.append(f"Market: {row.get('market', 'N/A')}")
        lines.append(f"List Date: {row.get('list_date', 'N/A')}")

    if daily_basic is not None and not daily_basic.empty:
        # Use the most recent available date
        row = daily_basic.iloc[0]
        lines.append(f"Close: {row.get('close', 'N/A')}")
        lines.append(f"PE Ratio: {row.get('pe', 'N/A')}")
        lines.append(f"PB Ratio: {row.get('pb', 'N/A')}")
        lines.append(f"PS Ratio: {row.get('ps', 'N/A')}")
        lines.append(f"Turnover Rate: {row.get('turnover_rate', 'N/A')}")
        lines.append(f"Volume Ratio: {row.get('volume_ratio', 'N/A')}")
        mv = row.get("total_mv")
        if mv:
            lines.append(f"Total Market Cap: {mv / 10000:.2f} (100M CNY)")
        circ = row.get("circ_mv")
        if circ:
            lines.append(f"Circulating Market Cap: {circ / 10000:.2f} (100M CNY)")

    if not lines:
        return f"No fundamentals data found for symbol '{ticker}'"

    header = f"# Company Fundamentals for {ticker.upper()}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + "\n".join(lines)


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get balance sheet data from Tushare."""
    ts_code = resolve_tushare_code(ticker)

    try:
        pro = get_pro_api()
        params = {
            "ts_code": ts_code,
            "fields": "ts_code,ann_date,end_date,report_type,"
                      "total_assets,total_liab,total_hldr_eqy_exc_min_int,"
                      "total_cur_assets,total_cur_liab,"
                      "money_cap,inventories,accounts_receiv,"
                      "fix_assets,goodwill,long_borr",
        }
        if curr_date:
            params["end_date"] = format_date(curr_date)
        df = pro.balancesheet(**params)
    except Exception as e:
        handle_tushare_error(e, f"balancesheet({ts_code})")

    if df is None or df.empty:
        return f"No balance sheet data found for symbol '{ticker}'"

    # Filter by report type (individual vs consolidated) - prefer consolidated
    if "report_type" in df.columns:
        consolidated = df[df["report_type"] == "1"]
        if not consolidated.empty:
            df = consolidated

    csv_string = df.to_csv(index=False)

    header = f"# Balance Sheet data for {ticker.upper()} ({freq})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get cash flow data from Tushare."""
    ts_code = resolve_tushare_code(ticker)

    try:
        pro = get_pro_api()
        params = {
            "ts_code": ts_code,
            "fields": "ts_code,ann_date,end_date,report_type,"
                      "n_cashflow_act,n_cashflow_inv_act,n_cash_flows_fnc_act,"
                      "c_fr_sale_sg,c_pay_acq_const_fiamt,c_pay_dist_dpcp_int_exp,"
                      "free_cashflow",
        }
        if curr_date:
            params["end_date"] = format_date(curr_date)
        df = pro.cashflow(**params)
    except Exception as e:
        handle_tushare_error(e, f"cashflow({ts_code})")

    if df is None or df.empty:
        return f"No cash flow data found for symbol '{ticker}'"

    if "report_type" in df.columns:
        consolidated = df[df["report_type"] == "1"]
        if not consolidated.empty:
            df = consolidated

    csv_string = df.to_csv(index=False)

    header = f"# Cash Flow data for {ticker.upper()} ({freq})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get income statement data from Tushare."""
    ts_code = resolve_tushare_code(ticker)

    try:
        pro = get_pro_api()
        params = {
            "ts_code": ts_code,
            "fields": "ts_code,ann_date,end_date,report_type,"
                      "revenue,oper_cost,total_profit,n_income,"
                      "n_income_attr_p,gross_profit_margin,"
                      "sell_exp,admin_exp,rd_exp,fin_exp",
        }
        if curr_date:
            params["end_date"] = format_date(curr_date)
        df = pro.income(**params)
    except Exception as e:
        handle_tushare_error(e, f"income({ts_code})")

    if df is None or df.empty:
        return f"No income statement data found for symbol '{ticker}'"

    if "report_type" in df.columns:
        consolidated = df[df["report_type"] == "1"]
        if not consolidated.empty:
            df = consolidated

    csv_string = df.to_csv(index=False)

    header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
