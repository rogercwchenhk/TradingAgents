from datetime import datetime
from typing import Annotated

import pandas as pd
from futu import KLType, AuType, RET_ERROR

from .futu_opend_common import _get_quote_context, resolve_futu_code, FutuRateLimitError


def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    from dateutil.relativedelta import relativedelta

    best_ind_params = {
        "close_50_sma": "50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.",
        "close_200_sma": "200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.",
        "close_10_ema": "10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.",
        "macd": "MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.",
        "macds": "MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.",
        "macdh": "MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.",
        "rsi": "RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.",
        "boll": "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.",
        "boll_ub": "Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.",
        "boll_lb": "Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.",
        "atr": "ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.",
        "vwma": "VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.",
        "mfi": "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals.",
    }

    if indicator not in best_ind_params:
        raise ValueError(f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}")

    futu_code = resolve_futu_code(symbol)
    ctx = _get_quote_context()

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    buffer_days = look_back_days + 300
    start_date = (curr_date_dt - relativedelta(days=buffer_days)).strftime("%Y-%m-%d")

    ret, data, _ = ctx.request_history_kline(
        futu_code,
        start=start_date,
        end=curr_date,
        ktype=KLType.K_DAY,
        autype=AuType.QFQ,
    )

    if ret == RET_ERROR:
        msg = str(data)
        if "rate limit" in msg.lower() or "frequency" in msg.lower():
            raise FutuRateLimitError(msg)
        return f"Error retrieving data for indicator {indicator}: {msg}"

    if data is None or data.empty:
        return f"No data found for {symbol} to calculate {indicator}"

    df = data.rename(columns={"time_key": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    df = _calculate_indicator(df, indicator)

    if indicator in df.columns:
        df = df[["Date", indicator]].dropna()
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        before = curr_date_dt - relativedelta(days=look_back_days)
        mask = (pd.to_datetime(df["Date"]) >= before) & (pd.to_datetime(df["Date"]) <= curr_date_dt)
        df = df[mask]

        ind_string = ""
        for _, row in df.iterrows():
            ind_string += f"{row['Date']}: {row[indicator]}\n"

        if not ind_string:
            ind_string = "No data available for the specified date range.\n"

        result_str = (
            f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
            + ind_string + "\n\n"
            + best_ind_params.get(indicator, "No description available.")
        )
        return result_str
    else:
        return f"Error: Failed to calculate indicator {indicator} for {symbol}"


def _calculate_indicator(df: pd.DataFrame, indicator: str) -> pd.DataFrame:
    if indicator == "close_50_sma":
        df[indicator] = df["Close"].rolling(window=50).mean()
    elif indicator == "close_200_sma":
        df[indicator] = df["Close"].rolling(window=200).mean()
    elif indicator == "close_10_ema":
        df[indicator] = df["Close"].ewm(span=10, adjust=False).mean()
    elif indicator in ("macd", "macds", "macdh"):
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        if indicator == "macd":
            df[indicator] = macd_line
        elif indicator == "macds":
            df[indicator] = signal_line
        else:
            df[indicator] = histogram
    elif indicator == "rsi":
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df[indicator] = 100 - (100 / (1 + rs))
    elif indicator in ("boll", "boll_ub", "boll_lb"):
        sma20 = df["Close"].rolling(window=20).mean()
        std20 = df["Close"].rolling(window=20).std()
        if indicator == "boll":
            df[indicator] = sma20
        elif indicator == "boll_ub":
            df[indicator] = sma20 + 2 * std20
        else:
            df[indicator] = sma20 - 2 * std20
    elif indicator == "atr":
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df[indicator] = tr.rolling(window=14).mean()
    elif indicator == "vwma":
        df[indicator] = (df["Close"] * df["Volume"]).rolling(window=20).sum() / df["Volume"].rolling(window=20).sum()
    elif indicator == "mfi":
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        money_flow = typical_price * df["Volume"]
        delta_tp = typical_price.diff()
        positive_flow = money_flow.where(delta_tp > 0, 0.0)
        negative_flow = money_flow.where(delta_tp < 0, 0.0)
        positive_sum = positive_flow.rolling(window=14).sum()
        negative_sum = negative_flow.rolling(window=14).sum()
        money_ratio = positive_sum / negative_sum
        df[indicator] = 100 - (100 / (1 + money_ratio))
    else:
        raise ValueError(f"Indicator {indicator} is not supported by Futu OpenD provider")

    return df
