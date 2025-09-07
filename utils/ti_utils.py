import numpy as np
from typing import List
import math

def price_rate_of_change(prices: List[float], window: int) -> float:
    return (prices[-1] / prices[-window]) - 1


def relative_strength_index(prices: List[float], window: int) -> float:
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gain[-window:])
    avg_loss = np.mean(loss[-window:])
    rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')

    return 100 - (100 / (1 + rs))


def stochastic_oscillator(prices: List[float], window: int) -> float:
    recent_prices = prices[-window:]
    highest_high = max(recent_prices)
    lowest_low = min(recent_prices)
    return 100 * (prices[-1] - lowest_low) / (highest_high - lowest_low)


def calculate_macd(prices: List[float], days26: int, days12: int, signal_window: int) -> tuple:
    fast_ma = np.mean(prices[-days12:])
    slow_ma = np.mean(prices[-days26:])
    macd_line = fast_ma - slow_ma

    # simple moving average for the signal line approximation
    early_window = prices[-(days26 + signal_window - 1):-signal_window+1]
    late_window = prices[-signal_window:]
    signal_line = np.mean(early_window) - np.mean(late_window)

    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist


def calculate_atr(results: List[dict], period: int) -> float:
    if len(results) < period:
        raise ValueError("Insufficient data for ATR calculation.")

    tr_list = []
    for i in range(1, period):
        curr = results[i]
        prev = results[i - 1]

        high = curr["h"]
        low = curr["l"]
        prev_close = prev["c"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        tr_list.append(tr)

    return np.mean(tr_list)


def round_to_sf(value: float, sig_figs: int = 3) -> float:
    if value == 0:
        return 0
    scale = math.pow(10, sig_figs - math.ceil(math.log10(abs(value))))
    return round(value * scale) / scale
