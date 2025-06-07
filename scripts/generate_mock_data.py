import json
import random
from datetime import datetime, timedelta

def generate_mock_ohlcv_data(days=60, start_price=100.0):
    """
    Generate synthetic OHLCV data for backtesting and testing strategies.
    """
    data = []
    current_price = start_price

    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).strftime('%Y-%m-%d')
        open_price = current_price
        high_price = open_price + random.uniform(0.5, 3.0)
        low_price = open_price - random.uniform(0.5, 3.0)
        close_price = random.uniform(low_price, high_price)
        volume = random.randint(100000, 1000000)

        data.append({
            "date": date,
            "o": round(open_price, 2),
            "h": round(high_price, 2),
            "l": round(low_price, 2),
            "c": round(close_price, 2),
            "v": volume
        })

        current_price = close_price  # simulate price progression

    return data

# Generate and save to JSON for inspection
mock_data = generate_mock_ohlcv_data()
file_path = "/mnt/data/mock_ohlcv_data.json"
with open(file_path, "w") as f:
    json.dump(mock_data, f, indent=2)

file_path
