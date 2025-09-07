# services/intelligence/strategies/percentage_strategy.py

class PercentageStrategy:
    def __init__(self, profit_pct=10.0, stop_pct=5.0):
        self.profit_pct = profit_pct / 100
        self.stop_pct = stop_pct / 100

    def generate_trade_plan(self, historical_data: list[dict], ticker: str) -> dict:
        """
        Generates a trade plan using fixed percentage stop loss / take profit.
        """
        entry_price = historical_data[-1]['c']
        stop_loss = round(entry_price * (1 - self.stop_pct), 2)
        take_profit = round(entry_price * (1 + self.profit_pct), 2)

        return {
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "expected_profit": round(take_profit - entry_price, 2),
            "expected_loss": round(entry_price - stop_loss, 2),
            "profit_pct": self.profit_pct * 100,
            "stop_pct": self.stop_pct * 100,
        }
