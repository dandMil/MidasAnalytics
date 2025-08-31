# utils/ta_helpers.py
# def fetch_sample_ohlcv(ticker: str):
#     """
#     Simulates sample OHLCV data.
#     """
#     return [
#         {"o": 100, "h": 105, "l": 99, "c": 102, "v": 1000000},
#         {"o": 102, "h": 106, "l": 101, "c": 104, "v": 1200000},
#         {"o": 104, "h": 108, "l": 103, "c": 107, "v": 1100000},
#         {"o": 107, "h": 109, "l": 106, "c": 108, "v": 1150000},
#         {"o": 108, "h": 110, "l": 107, "c": 109, "v": 1250000},
#         # Add more as needed
#     ]
#
#

def fetch_sample_ohlcv(ticker: str) -> list[dict]:
    import random
    # Generate mock data for 30 days
    return [{
        "o": 100 + random.uniform(-2, 2),
        "h": 105 + random.uniform(-2, 2),
        "l": 95 + random.uniform(-2, 2),
        "c": 100 + random.uniform(-2, 2),
        "v": random.randint(1000000, 5000000)
    } for _ in range(30)]
