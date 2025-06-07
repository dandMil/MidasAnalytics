# utils/mock_data_generator.py

import random
from datetime import datetime, timedelta

def generate_mock_ohlcv(days=100):
    """
    Generate mock OHLCV data for backtesting.
    Each day includes open, high, low, close, volume, and timestamp.
    """
    data = []
    base_price = 100.0
    base_volume = 1_000_000
    current_date = datetime.now()

    for i in range(days):
        date = current_date - timedelta(days=days - i)
        open_price = base_price + random.uniform(-2, 2)
        high = open_price + random.uniform(0, 3)
        low = open_price - random.uniform(0, 3)
        close = random.uniform(low, high)
        volume = base_volume + random.randint(-100_000, 100_000)

        data.append({
            "t": date.strftime("%Y-%m-%d"),
            "o": round(open_price, 2),
            "h": round(high, 2),
            "l": round(low, 2),
            "c": round(close, 2),
            "v": volume
        })

        base_price = close  # carry over for continuity

    return data
