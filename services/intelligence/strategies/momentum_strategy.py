import pandas as pd

class MomentumStrategy:
    def apply(self, df: pd.DataFrame, ticker: str):
        if len(df) < 11:
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
        recent = df['close'].iloc[-1]
        past = df['close'].iloc[-10]
        change = (recent - past) / past

        signal = "buy" if change > 0.05 else "sell" if change < -0.05 else "hold"
        stop_loss = round(recent * 0.97, 2)
        take_profit = round(recent * 1.05, 2)

        log_entry = {
            "date": str(df.index[-1]) if df.index.name else "N/A",
            "action": signal,
            "price": round(recent, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }

        result = {
            "ticker": ticker,
            "signal": signal,
            "price": round(recent, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "expected_profit": round(take_profit - recent, 2),
            "expected_loss": round(recent - stop_loss, 2),
            "log": [log_entry]
        }

        print(f"[MomentumStrategy] {ticker} result: {result}")
        return result


class MeanReversionStrategy:
    def __init__(self, rsi_threshold=70, bb_window=20, bb_std=2):
        self.rsi_threshold = rsi_threshold
        self.bb_window = bb_window
        self.bb_std = bb_std

    def apply(self, df: pd.DataFrame, ticker: str):
        if len(df) < self.bb_window:
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
        df['sma'] = df['close'].rolling(window=self.bb_window).mean()
        df['std'] = df['close'].rolling(window=self.bb_window).std()
        df['upper_band'] = df['sma'] + self.bb_std * df['std']
        df['lower_band'] = df['sma'] - self.bb_std * df['std']

        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        price = latest['close']
        rsi = latest['rsi']
        upper_band = latest['upper_band']
        lower_band = latest['lower_band']

        signal = "hold"
        if price > upper_band and rsi > self.rsi_threshold:
            signal = "sell"
        elif price < lower_band and rsi < (100 - self.rsi_threshold):
            signal = "buy"

        stop_loss = round(price * 0.97, 2) if signal == "buy" else round(price * 1.03, 2)
        take_profit = round(price * 1.05, 2) if signal == "buy" else round(price * 0.95, 2)

        log_entry = {
            "date": str(df.index[-1]) if df.index.name else "N/A",
            "action": signal,
            "price": round(price, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }

        result = {
            "ticker": ticker,
            "strategy": "Mean Reversion",
            "signal": signal,
            "price": round(price, 2),
            "rsi": round(rsi, 2),
            "upper_band": round(upper_band, 2),
            "lower_band": round(lower_band, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "expected_profit": round(take_profit - price, 2),
            "expected_loss": round(price - stop_loss, 2),
            "log": [log_entry]
        }

        print(f"[MeanReversionStrategy] {ticker} result: {result}")
        return result
