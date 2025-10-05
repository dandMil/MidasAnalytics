# services/ticker_universe_service.py

import csv
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class TickerUniverseService:
    """Service to manage the universe of available stock tickers."""
    
    def __init__(self, csv_file_path: str = "data/us_stock_universe.csv"):
        self.csv_file_path = csv_file_path
        self._tickers_cache = None
        self._last_loaded = None
        self._cache_duration = timedelta(hours=24)  # Cache for 24 hours
    
    def load_tickers_from_csv(self) -> List[Dict]:
        """Load tickers from CSV file."""
        if not os.path.exists(self.csv_file_path):
            print(f"❌ Ticker universe file not found: {self.csv_file_path}")
            print("💡 Run scripts/fetch_ticker_universe.py to create the universe file")
            return []
        
        tickers = []
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    tickers.append(row)
            
            print(f"✅ Loaded {len(tickers)} tickers from {self.csv_file_path}")
            return tickers
            
        except Exception as e:
            print(f"❌ Error loading tickers from CSV: {e}")
            return []
    
    def get_tickers(self, force_reload: bool = False) -> List[Dict]:
        """Get tickers with caching."""
        now = datetime.now()
        
        # Check if cache is valid
        if (self._tickers_cache is not None and 
            self._last_loaded is not None and 
            not force_reload and
            (now - self._last_loaded) < self._cache_duration):
            return self._tickers_cache
        
        # Load from CSV
        self._tickers_cache = self.load_tickers_from_csv()
        self._last_loaded = now
        
        return self._tickers_cache
    
    def get_tickers_by_exchange(self, exchange: str = None) -> List[Dict]:
        """Get tickers filtered by exchange."""
        all_tickers = self.get_tickers()
        
        if not exchange:
            return all_tickers
        
        return [ticker for ticker in all_tickers 
                if ticker.get('primary_exchange', '').upper() == exchange.upper()]
    
    def get_tickers_by_type(self, ticker_type: str = None) -> List[Dict]:
        """Get tickers filtered by type."""
        all_tickers = self.get_tickers()
        
        if not ticker_type:
            return all_tickers
        
        return [ticker for ticker in all_tickers 
                if ticker.get('type', '').upper() == ticker_type.upper()]
    
    def get_ticker_symbols(self, limit: int = None) -> List[str]:
        """Get just the ticker symbols."""
        all_tickers = self.get_tickers()
        symbols = [ticker['ticker'] for ticker in all_tickers if ticker.get('ticker')]
        
        if limit:
            return symbols[:limit]
        
        return symbols
    
    def get_exchanges(self) -> List[str]:
        """Get list of unique exchanges."""
        all_tickers = self.get_tickers()
        exchanges = set()
        
        for ticker in all_tickers:
            exchange = ticker.get('primary_exchange', '')
            if exchange:
                exchanges.add(exchange)
        
        return sorted(list(exchanges))
    
    def get_ticker_types(self) -> List[str]:
        """Get list of unique ticker types."""
        all_tickers = self.get_tickers()
        types = set()
        
        for ticker in all_tickers:
            ticker_type = ticker.get('type', '')
            if ticker_type:
                types.add(ticker_type)
        
        return sorted(list(types))
    
    def get_universe_stats(self) -> Dict:
        """Get statistics about the ticker universe."""
        all_tickers = self.get_tickers()
        
        if not all_tickers:
            return {"error": "No tickers loaded"}
        
        exchanges = {}
        types = {}
        
        for ticker in all_tickers:
            exchange = ticker.get('primary_exchange', 'Unknown')
            ticker_type = ticker.get('type', 'Unknown')
            
            exchanges[exchange] = exchanges.get(exchange, 0) + 1
            types[ticker_type] = types.get(ticker_type, 0) + 1
        
        return {
            "total_tickers": len(all_tickers),
            "exchanges": exchanges,
            "types": types,
            "last_updated": self._last_loaded.isoformat() if self._last_loaded else None
        }

# Global instance
ticker_universe = TickerUniverseService()
