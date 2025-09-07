# services/intelligence/strategies/volatility_strategy.py

class VolatilityStrategy:
    def __init__(self, atr_multiplier_profit=3.0, atr_multiplier_loss=2.0):
        self.atr_profit = atr_multiplier_profit
        self.atr_loss = atr_multiplier_loss

    def generate_trade_plan(self, historical_data: list[dict], ticker: str) -> dict:
        """
        Generates a trade plan using ATR-based stop loss and take profit.
        Expects historical_data to be a list of bars with keys: 'h', 'l', 'c'
        """
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
