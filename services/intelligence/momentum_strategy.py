from typing import List


class MomentumStrategy:
    """
    Basic momentum-based strategy using price rate of change (ROC) and MACD.
    Suitable for assets with upward price acceleration.
    """

    def __init__(self, roc_threshold: float = 0.05, macd_positive: bool = True):
        self.roc_threshold = roc_threshold  # Example: 5% threshold
        self.macd_positive = macd_positive

    def generate_signal(self, closing_prices: List[float], macd_line: float, signal_line: float, roc: float) -> str:
        """
        Generate a trade signal based on momentum indicators.

        Parameters:
        - closing_prices: Historical close prices (most recent last)
        - macd_line: Current MACD line value
        - signal_line: Current Signal line value
        - roc: Current Rate of Change

        Returns: 'BUY', 'SELL', or 'HOLD'
        """
        if len(closing_prices) < 15:
            return 'HOLD'  # Not enough data

        # Check MACD crossover and ROC threshold
        if macd_line > signal_line and roc > self.roc_threshold:
            return 'BUY'
        elif macd_line < signal_line and roc < -self.roc_threshold:
            return 'SELL'
        else:
            return 'HOLD'

    def describe(self):
        return {
            "strategy": "Momentum",
            "criteria": {
                "MACD crossover": "MACD > Signal Line",
                "ROC threshold": f"ROC > {self.roc_threshold * 100:.1f}%"
            }
        }
