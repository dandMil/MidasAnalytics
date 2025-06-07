from abc import ABC, abstractmethod
from typing import List, Dict

class StrategyInterface(ABC):
    @abstractmethod
    def generate_trade_plan(self, historical_data: List[Dict], ticker: str) -> Dict:
        """
        Given historical OHLCV data, return a trade plan containing:
        - entry_price
        - take_profit
        - stop_loss
        - signal_strength
        """
        pass
