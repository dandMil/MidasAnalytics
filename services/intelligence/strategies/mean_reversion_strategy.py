# services/intelligence/strategies/mean_reversion_strategy.py

import pandas as pd
from ..interfaces.strategy_interface import StrategyInterface


class MeanReversionStrategy(StrategyInterface):
    def __init__(self, rsi_threshold=70, bb_window=20, bb_std=2):
        self.rsi_threshold = rsi_threshold
        self.bb_window = bb_window
        self.bb_std = bb_std

    # def generate_trade_plan(self, historical_data: list[dict], ticker: str) -> dict:
    #     df = pd.DataFrame(historical_data)
    #     df.columns = df.columns.str.lower()
    #
    #     # Convert timestamp to datetime if available
    #     if 't' in df.columns:
    #         df['date'] = pd.to_datetime(df['t'], unit='ms')
    #         df.set_index('date', inplace=True)
    #
    #     return self.apply(df, ticker)

    def generate_trade_plan(self, historical_data: list[dict], ticker: str) -> dict:
        df = pd.DataFrame(historical_data)
        df.columns = df.columns.str.lower()
        print(f'MEAN REV COLUMNS {df.columns}')
        # Log raw timestamp values from Polygon
        if 't' in df.columns:
            print(f"[{ticker}] Raw timestamps (ms) from Polygon: {df['t'].tolist()[:5]}")

            df['date'] = pd.to_datetime(df['t'], unit='ms')
            print(f"[{ticker}] Converted datetime index: {df['date'].tolist()[:5]}")

            df.set_index('date', inplace=True)

        return self.apply(df, ticker)


    def apply(self, df: pd.DataFrame, ticker: str):
        if df.empty or len(df) < self.bb_window + 1:
            return self._hold_response(ticker, df)

        df = df.copy()
        df['sma'] = df['close'].rolling(window=self.bb_window).mean()
        df['std'] = df['close'].rolling(window=self.bb_window).std()
        df['upper_band'] = df['sma'] + self.bb_std * df['std']
        df['lower_band'] = df['sma'] - self.bb_std * df['std']

        # RSI calculation
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        signal = "hold"
        price = latest['close']
        rsi = latest['rsi']
        upper_band = latest['upper_band']
        lower_band = latest['lower_band']

        if price > upper_band and rsi > self.rsi_threshold:
            signal = "sell"
        elif price < lower_band and rsi < (100 - self.rsi_threshold):
            signal = "buy"

        stop_loss = price * 0.97 if signal == "buy" else price * 1.03 if signal == "sell" else None
        take_profit = price * 1.05 if signal == "buy" else price * 0.95 if signal == "sell" else None

        log_entry = {
            "date": str(df.index[-1]) if df.index.name else "N/A",
            "action": signal,
            "price": round(price, 2),
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "take_profit": round(take_profit, 2) if take_profit else None,
        }

        result = {
            "ticker": ticker,
            "strategy": "MeanReversionStrategy",
            "signal": signal,
            "price": round(price, 2),
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "take_profit": round(take_profit, 2) if take_profit else None,
            "expected_profit": round(take_profit - price, 2) if take_profit else 0.0,
            "expected_loss": round(price - stop_loss, 2) if stop_loss else 0.0,
            "log": [log_entry]
        }

        print(f"[MeanReversionStrategy] {ticker} result: {result}")
        return result

    def _hold_response(self, ticker: str, df: pd.DataFrame):
        price = df['close'].iloc[-1] if not df.empty else None
        return {
            "ticker": ticker,
            "strategy": "MeanReversionStrategy",
            "signal": "hold",
            "price": round(price, 2) if price else None,
            "stop_loss": None,
            "take_profit": None,
            "expected_profit": 0.0,
            "expected_loss": 0.0,
            "log": []
        }
