# services/intelligence/agent_planner.py

from services.intelligence.strategies.volatility_strategy import VolatilityStrategy
from services.intelligence.strategies.percentage_strategy import PercentageStrategy
from services.intelligence.strategies.momentum_strategy import MomentumStrategy
from services.intelligence.strategies.mean_reversion_strategy import MeanReversionStrategy

from services.backtesting.backtest_engine import BacktestEngine


class AgentPlanner:
    def __init__(self):
        self.strategies = {
            "VolatilityStrategy": VolatilityStrategy(),
            "PercentageStrategy": PercentageStrategy(),
            "MomentumStrategy": MomentumStrategy(),
            "MeanReversionStrategy": MeanReversionStrategy()
        }
        self.backtester = BacktestEngine()

    def plan_trade(self, historical_data: list[dict], ticker: str) -> dict:
        """
        Determines the appropriate strategy based on price action and volatility.
        """
        if not historical_data or len(historical_data) < 20:
            raise ValueError("Insufficient historical data for strategy planning.")

        strategy_name = self._select_strategy(historical_data)
        strategy = self.strategies[strategy_name]

        print(f"[AgentPlanner] Selected strategy: {strategy_name}")
        trade_plan = strategy.generate_trade_plan(historical_data, ticker)

        return {
            "ticker": ticker,
            "strategy": strategy_name,
            "trade_plan": trade_plan
        }

    def _select_strategy(self, data: list[dict]) -> str:
        """
        Strategy selection logic based on basic technical analysis heuristics.
        """

        recent_close = data[-1]['c']
        range_today = data[-1]['h'] - data[-1]['l']
        avg_range = sum((bar['h'] - bar['l']) for bar in data[-14:]) / 14

        # Momentum: strong upward movement over past N days
        momentum = data[-1]['c'] - data[-10]['c']

        # Mean reversion: price far above/below moving average (Bollinger proxy)
        close_prices = [bar['c'] for bar in data[-20:]]
        mean_price = sum(close_prices) / len(close_prices)
        deviation = abs(recent_close - mean_price) / mean_price

        if deviation > 0.1:
            return "MeanReversionStrategy"
        elif momentum > 0.05 * recent_close:
            return "MomentumStrategy"
        elif range_today > 1.5 * avg_range:
            return "VolatilityStrategy"
        else:
            return "PercentageStrategy"
