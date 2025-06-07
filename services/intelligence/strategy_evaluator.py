import pandas as pd
# from services.market_data.polygon_service import fetch_polygon_ohlcv
from utils.polygon_client import get_price_history

from services.backtesting.backtest_engine import BacktestEngine
from services.intelligence.strategies.mean_reversion_strategy import MeanReversionStrategy
from services.intelligence.strategies.volatility_strategy import VolatilityStrategy
from services.intelligence.strategies.percentage_strategy import PercentageStrategy

class StrategyEvaluator:
    def __init__(self):
        self.strategies = [
            MeanReversionStrategy(),
            VolatilityStrategy(),
            PercentageStrategy()
        ]
        self.backtest_engine = BacktestEngine()

    def run_all_backtests(self, ticker: str, days: int = 60):
        historical_data = get_price_history(ticker, days=days)

        if not historical_data or len(historical_data) < 20:
            print(f"[Evaluator] Not enough data for {ticker}")
            return []

        results = []
        for strategy in self.strategies:
            try:
                result = self.backtest_engine.run(strategy, historical_data, ticker)
                results.append({"strategy": strategy.__class__.__name__, "result": result})
            except Exception as e:
                print(f"[Evaluator] Error evaluating {strategy.__class__.__name__} on {ticker}: {e}")

        results.sort(key=lambda r: r["result"].get("total_return", -float('inf')), reverse=True)
        return results
