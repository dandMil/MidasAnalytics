from agent.interfaces import StrategyInterface
import pandas as pd
import numpy as np

class MeanReversionStrategy(StrategyInterface):
    """
    This strategy uses Bollinger Bands to detect price overextensions and RSI as confirmation
    for potential mean reversion trades.
    """

    def __init__(self, rsi_threshold=70, bb_window=20, bb_std=2):
        self.rsi_threshold = rsi_threshold
        self.bb_window = bb_window
        self.bb_std = bb_std

    def apply(self, df: pd.DataFrame, ticker: str):
        """
        Apply mean reversion logic using Bollinger Bands + RSI.

        Args:
            df (pd.DataFrame): OHLCV data with 'close' column.
            ticker (str): Ticker symbol.

        Returns:
            dict: signal, stop_loss, take_profit, strategy_name
        """

        df = df.copy()
        df['sma'] = df['close'].rolling(window=self.bb_window).mean()
        df['std'] = df['close'].rolling(window=self.bb_window).std()

        df['upper_band'] = df['sma'] + self.bb_std * df['std']
        df['lower_band'] = df['sma'] - self.bb_std * df['std']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]

        # Mean reversion: sell if above upper band and RSI high; buy if below lower band and RSI low
        signal = "hold"
        price = latest['close']
        rsi = latest['rsi']
        upper_band = latest['upper_band']
        lower_band = latest['lower_band']

        if price > upper_band and rsi > self.rsi_threshold:
            signal = "sell"
        elif price < lower_band and rsi < (100 - self.rsi_threshold):
            signal = "buy"

        # Simple profit/loss band
        stop_loss = price * 0.97 if signal == "buy" else price * 1.03
        take_profit = price * 1.05 if signal == "buy" else price * 0.95

        return {
            "ticker": ticker,
            "strategy": "Mean Reversion",
            "signal": signal,
            "price": price,
            "rsi": round(rsi, 2),
            "upper_band": round(upper_band, 2),
            "lower_band": round(lower_band, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2)
        }
