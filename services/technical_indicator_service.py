# services/technical_indicator_service.py

from utils.polygon_client import get_price_history
import numpy as np
import pandas as pd
import ta

from utils.polygon_client import get_price_history
import pandas as pd
import ta
from utils.ti_utils import (
    stochastic_oscillator,
    price_rate_of_change,
    relative_strength_index,
    calculate_macd,
    calculate_atr,
    round_to_sf
)
def calculate_technical_indicators(ticker: str, asset_type: str = "stock"):
    """
    Calculate technical indicators using Polygon and generate a trading signal.
    """

    if asset_type.lower() == "crypto":
        ticker = f"X:{ticker.upper()}USD"

    try:
        data = get_price_history(ticker, days=60)
        bars = data.get("results", [])
        if not bars or len(bars) < 30:
            return {"error": "Not enough data."}

        # Convert bars to DataFrame
        df = pd.DataFrame(bars)
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        df['Date'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)

        close_prices = df['Close'].values[::-1]  # Reverse for consistency

        # Compute technical indicators
        df['macd'] = ta.trend.MACD(df['Close']).macd()
        df['macd_signal'] = ta.trend.MACD(df['Close']).macd_signal()
        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['roc'] = ta.momentum.ROCIndicator(df['Close'], window=14).roc()
        df['so'] = stochastic_oscillator(df)
        df['atr'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()

        # Get latest values
        macd_line = df['macd'].iloc[-1]
        signal_line = df['macd_signal'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        prc = df['roc'].iloc[-1]
        so = df['so'].iloc[-1]
        atr = df['atr'].iloc[-1]

        indicator_scores = {
            "MACD": 1 if macd_line > signal_line else -1,
            "RSI": 1 if rsi < 30 else -1 if rsi > 70 else 0,
            "SO": 1 if so < 20 else -1 if so > 80 else 0,
            "PRC": 1 if prc > 0 else -1
        }
        print('INDICATOR SCORES ',indicator_scores)
        signal = compute_signal(indicator_scores, ticker)

        return {
            "ticker": ticker,
            "market_price": round_to_sf(close_prices[0], 2),
            "macd": round_to_sf(macd_line, 2),
            "macd_signal": round_to_sf(signal_line, 2),
            "rsi": round_to_sf(rsi, 2),
            "stochastic_oscillator": round_to_sf(so, 2),
            "price_rate_of_change": round_to_sf(prc, 2),
            "atr": round_to_sf(atr, 2),
            "indicator_scores": indicator_scores,
            "signal": signal
        }

    except Exception as e:
        return {"error": str(e)}


def compute_signal(score_map, ticker):
    weights = {
        "MACD": 0.5,
        "PRC": 0.3,
        "RSI": 0.2,
        "SO": 0.4
    }

    overall_score = sum(score_map[k] * weights[k] for k in score_map)

    if overall_score > 0:
        return "BULLISH"
    elif overall_score < 0:
        return "BEARISH"
    else:
        return "NEUTRAL"

def round_to_sf(value, sig_figs):
    if value == 0:
        return 0
    d = np.ceil(np.log10(abs(value)))
    power = sig_figs - int(d)
    magnitude = 10 ** power
    return round(value * magnitude) / magnitude

def stochastic_oscillator(df, window=14):
    low_min = df['Low'].rolling(window=window).min()
    high_max = df['High'].rolling(window=window).max()
    so = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    return so
