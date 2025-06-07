import pandas as pd

class VolatilityStrategy:
    def __init__(self, atr_multiplier_profit=3.0, atr_multiplier_loss=2.0):
        self.atr_profit = atr_multiplier_profit
        self.atr_loss = atr_multiplier_loss

    def generate_trade_plan(self, historical_data: list[dict], ticker: str) -> dict:
        atr = self._calculate_atr(historical_data)
        entry_price = historical_data[-1]['c']
        stop_loss = round(entry_price - self.atr_loss * atr, 2)
        take_profit = round(entry_price + self.atr_profit * atr, 2)

        return {
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "expected_profit": round(take_profit - entry_price, 2),
            "expected_loss": round(entry_price - stop_loss, 2),
            "atr": round(atr, 2),
        }

    def _calculate_atr(self, data: list[dict], period=14) -> float:
        trs = []
        for i in range(1, min(len(data), period + 1)):
            high = data[i]['h']
            low = data[i]['l']
            prev_close = data[i - 1]['c']
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return sum(trs) / len(trs) if trs else 0.0

    def apply(self, df: pd.DataFrame, ticker: str):
        if len(df) < 2:
            return {
                "signal": "hold",
                "price": None,
                "stop_loss": None,
                "take_profit": None,
                "expected_profit": None,
                "expected_loss": None,
                "log": []
            }

        df = df.copy()
        df['atr'] = df['high'].sub(df['low']).rolling(window=14).mean()

        price = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1]
        stop_loss = round(price - self.atr_loss * atr, 2)
        take_profit = round(price + self.atr_profit * atr, 2)

        signal = "hold"
        if len(df) % 2 == 0:
            signal = "buy"
        elif len(df) % 3 == 0:
            signal = "sell"
        if 't' in df.columns:
            df['date'] = pd.to_datetime(df['t'], unit='ms')  # convert Polygon ms timestamp to datetime
            df.set_index('date', inplace=True)

        result = {
            "ticker": ticker,
            "signal": signal,
            "price": round(price, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "expected_profit": round(take_profit - price, 2),
            "expected_loss": round(price - stop_loss, 2),
            "log": [
                {
                    "date": str(df.index[-1]) if df.index.name else "N/A",
                    "action": signal,
                    "price": round(price, 2),
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            ]
        }

        print(f"[VolatilityStrategy] {ticker} result: {result}")

        return result
