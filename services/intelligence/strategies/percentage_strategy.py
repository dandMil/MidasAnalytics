# services/intelligence/strategies/percentage_strategy.py

import pandas as pd
from ..interfaces.strategy_interface import StrategyInterface

class PercentageStrategy(StrategyInterface):
    def __init__(self, profit_pct=0.10, loss_pct=0.05):
        self.profit_pct = profit_pct
        self.loss_pct = loss_pct

    def generate_trade_plan(self, historical_data: list[dict], ticker: str) -> dict:
        df = pd.DataFrame(historical_data)
        df.columns = df.columns.str.lower()
        return self.apply(df, ticker)

    def apply(self, df: pd.DataFrame, ticker: str):
        if df.empty:
            return self._hold_response(ticker, None)

        recent_price = df['c'].iloc[-1]
        signal = "buy"  # This strategy assumes always-buy; refinement is possible

        stop_loss = recent_price * (1 - self.loss_pct)
        take_profit = recent_price * (1 + self.profit_pct)
        result = {
            "ticker": ticker,
            "strategy": "PercentageStrategy",
            "signal": signal,
            "price": round(recent_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "expected_profit": round(take_profit - recent_price, 2),
            "expected_loss": round(recent_price - stop_loss, 2)
        }
        print(f"[VolatilityStrategy] {ticker} result: {result}")
        return result

    def _hold_response(self, ticker, price):
        return {
            "ticker": ticker,
            "strategy": "PercentageStrategy",
            "signal": "hold",
            "price": round(price, 2) if price else None,
            "stop_loss": None,
            "take_profit": None,
            "expected_profit": 0.0,
            "expected_loss": 0.0
        }
