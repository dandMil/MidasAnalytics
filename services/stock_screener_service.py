# services/stock_screener_service.py

import time
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.polygon_client import get_price_history, get_market_snapshot
import pandas as pd
import json
import os
import random
import logging

# Import ticker universe service
from services.ticker_universe_service import ticker_universe

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DURATION_HOURS = 48  # Temporarily increased to 48 hours  
CACHE_FILE = "cache/stock_screener_cache.json"
CHECKPOINT_FILE = "cache/screener_checkpoint.json"
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N tickers

def load_cache() -> Dict:
    """Load cached stock data"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
            if datetime.now() - cache_time < timedelta(hours=CACHE_DURATION_HOURS):
                print(f"📦 Using cached data (age: {datetime.now() - cache_time})")
                return cache_data.get('stock_data', {})
            else:
                print(f"⏰ Cache expired (age: {datetime.now() - cache_time})")
                return {}
    except Exception as e:
        print(f"⚠️ Error loading cache: {e}")
    return {}

def save_cache(stock_data: Dict):
    """Save stock data to cache"""
    try:
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'stock_data': stock_data
        }
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"💾 Cached {len(stock_data)} stocks for {CACHE_DURATION_HOURS} hours")
    except Exception as e:
        print(f"⚠️ Error saving cache: {e}")


def load_checkpoint() -> Optional[Dict]:
    """Load checkpoint data for batch mode resume"""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint_data = json.load(f)
            
            # Check if checkpoint is still valid (not older than cache duration)
            checkpoint_time = datetime.fromisoformat(checkpoint_data.get('timestamp', '1970-01-01'))
            if datetime.now() - checkpoint_time < timedelta(hours=CACHE_DURATION_HOURS):
                logger.info(f"📋 Found valid checkpoint from {checkpoint_time}")
                return checkpoint_data
            else:
                logger.info(f"⏰ Checkpoint expired (age: {datetime.now() - checkpoint_time})")
                return None
    except Exception as e:
        logger.warning(f"⚠️ Error loading checkpoint: {e}")
    return None


def save_checkpoint(processed_tickers: List[str], filters_hash: str, batch_id: str, stats: Dict):
    """Save checkpoint data for batch mode resume"""
    try:
        os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
        
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'batch_id': batch_id,
            'filters_hash': filters_hash,
            'processed_tickers': processed_tickers,
            'stats': stats
        }
        
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.debug(f"💾 Checkpoint saved: {len(processed_tickers)} tickers processed")
    except Exception as e:
        logger.error(f"⚠️ Error saving checkpoint: {e}")


def clear_checkpoint():
    """Clear checkpoint file"""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            logger.info("🗑️  Checkpoint cleared")
    except Exception as e:
        logger.error(f"⚠️ Error clearing checkpoint: {e}")


def get_filters_hash(filters: Dict) -> str:
    """Generate a hash of filters to match checkpoints"""
    import hashlib
    # Create a stable representation of filters (excluding batch_id and resume flag)
    filter_copy = {k: v for k, v in filters.items() 
                   if k not in ['batch_id']}  # batch_id excluded as it's auto-generated
    filter_str = json.dumps(filter_copy, sort_keys=True)
    return hashlib.md5(filter_str.encode()).hexdigest()[:8]

# Define sector tickers (fallback for when universe is not available)
SECTOR_TICKERS = {
    "tech": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "ADBE", "CRM",
        "ORCL", "INTC", "AMD", "QCOM", "AVGO", "TXN", "AMAT", "LRCX", "KLAC", "MCHP",
        "SNPS", "CDNS", "ANSS", "FTNT", "PANW", "CRWD", "ZS", "OKTA", "DDOG", "NET"
    ],
    "bio": [
        "GILD", "AMGN", "BIIB", "REGN", "VRTX", "ILMN", "MRNA", "BNTX", "PFE", "JNJ",
        "ABBV", "BMY", "LLY", "MRK", "TMO", "DHR", "ABT", "ISRG", "SYK", "MDT"
    ],
    "finance": [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK", "SCHW", "COF",
        "USB", "PNC", "TFC", "BK", "STT", "NTRS", "RF", "CFG", "HBAN", "FITB"
    ],
    "energy": [
        "XOM", "CVX", "COP", "EOG", "SLB", "PXD", "MPC", "VLO", "PSX", "KMI",
        "WMB", "OKE", "EPD", "ET", "ENB", "TRP", "PPL", "DUK", "SO", "NEE"
    ]
}

# SIC-based sector mapping (maps human-readable names to SIC CSV files)
SIC_SECTOR_MAPPING = {
    "tech_sic": {
        "csv_file": "data/sic_tickers/tech_tickers_by_sic.csv",
        "display_name": "Technology/AI",
        "fallback": "tech"
    },
    "energy_sic": {
        "csv_file": "data/sic_tickers/energy_tickers_by_sic.csv",
        "display_name": "Energy",
        "fallback": "energy"
    },
    "healthcare_sic": {
        "csv_file": "data/sic_tickers/healthcare_tickers_by_sic.csv",
        "display_name": "Healthcare/Biotech",
        "fallback": "bio"
    }
}

# Map predefined sector names to their SIC-based equivalents
# When "tech", "energy", or "bio" is selected, use SIC-based sector instead
PREDEFINED_TO_SIC_MAPPING = {
    "tech": "tech_sic",
    "energy": "energy_sic",
    "bio": "healthcare_sic"
}

def load_tickers_from_sic_csv(csv_file_path: str) -> List[str]:
    """
    Load ticker symbols from a SIC-based CSV file.
    
    Args:
        csv_file_path: Path to the SIC tickers CSV file (relative to project root)
        
    Returns:
        List of ticker symbols
    """
    # Resolve path relative to project root
    # Get the directory of this file (services/), go up one level to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    absolute_path = os.path.join(project_root, csv_file_path)
    
    # Also try the path as-is (in case it's already absolute)
    if not os.path.exists(absolute_path) and os.path.exists(csv_file_path):
        absolute_path = csv_file_path
    
    if not os.path.exists(absolute_path):
        logger.warning(f"⚠️  SIC CSV file not found: {absolute_path} (tried: {csv_file_path})")
        return []
    
    try:
        tickers = []
        with open(absolute_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('ticker', '').strip()
                if ticker:
                    tickers.append(ticker)
        
        logger.info(f"✅ Loaded {len(tickers)} tickers from {absolute_path}")
        return tickers
    except Exception as e:
        logger.error(f"❌ Error loading SIC CSV {absolute_path}: {e}")
        return []

def calculate_performance_percentage(current_price: float, historical_price: float) -> float:
    """Calculate performance percentage"""
    if historical_price == 0:
        return 0
    return ((current_price - historical_price) / historical_price) * 100

def calculate_adr_percentage(high: float, low: float, close: float) -> float:
    """Calculate Average Daily Range percentage"""
    if close == 0:
        return 0
    return ((high - low) / close) * 100

def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal).mean()
    return macd_line, macd_signal

def calculate_stochastic_oscillator(df: pd.DataFrame, window: int = 14):
    """Calculate Stochastic Oscillator"""
    low_min = df['Low'].rolling(window=window).min()
    high_max = df['High'].rolling(window=window).max()
    so = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    return so

def calculate_atr(df: pd.DataFrame, window: int = 14):
    """Calculate Average True Range"""
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=window).mean()
    return atr

def get_stock_performance_data(ticker: str, days_back: int = 180) -> Optional[Dict]:
    """Get stock performance data for screening"""
    try:
        # Get price history for 6 months
        bars = get_price_history(ticker, days=days_back)
        if not bars or len(bars) < 30:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        df['Date'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        # Get current price (most recent close)
        current_price = df['Close'].iloc[-1]
        
        # Calculate performance periods
        # 1 month (30 days)
        if len(df) >= 30:
            price_1m_ago = df['Close'].iloc[-30]
            performance_1m = calculate_performance_percentage(current_price, price_1m_ago)
        else:
            performance_1m = 0
            
        # 3 months (90 days)
        if len(df) >= 90:
            price_3m_ago = df['Close'].iloc[-90]
            performance_3m = calculate_performance_percentage(current_price, price_3m_ago)
        else:
            performance_3m = 0
            
        # 6 months (180 days)
        if len(df) >= 180:
            price_6m_ago = df['Close'].iloc[-180]
            performance_6m = calculate_performance_percentage(current_price, price_6m_ago)
        else:
            performance_6m = 0
        
        # Calculate ADR% (Average Daily Range) for last 30 days
        recent_df = df.tail(30)
        adr_percentages = []
        for _, row in recent_df.iterrows():
            adr_pct = calculate_adr_percentage(row['High'], row['Low'], row['Close'])
            adr_percentages.append(adr_pct)
        
        avg_adr_percentage = sum(adr_percentages) / len(adr_percentages) if adr_percentages else 0
        
        # Calculate RSI (14-day)
        rsi = calculate_rsi(df['Close'], window=14)
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50
        
        # Determine RSI signal
        if current_rsi < 30:
            rsi_signal = "OVERSOLD"
        elif current_rsi > 70:
            rsi_signal = "OVERBOUGHT"
        else:
            rsi_signal = "NEUTRAL"
        
        # Calculate additional technical indicators
        macd_line, macd_signal_line = calculate_macd(df['Close'])
        stochastic_osc = calculate_stochastic_oscillator(df)
        atr = calculate_atr(df)
        
        # Get latest values
        current_macd = macd_line.iloc[-1] if not macd_line.empty else 0
        current_macd_signal = macd_signal_line.iloc[-1] if not macd_signal_line.empty else 0
        current_stochastic = stochastic_osc.iloc[-1] if not stochastic_osc.empty else 50
        current_atr = atr.iloc[-1] if not atr.empty else 0
        
        # Calculate indicator scores (same logic as technical_indicator_service)
        indicator_scores = {
            "MACD": 1 if current_macd > current_macd_signal else -1,
            "RSI": 1 if current_rsi < 30 else -1 if current_rsi > 70 else 0,
            "SO": 1 if current_stochastic < 20 else -1 if current_stochastic > 80 else 0,
            "PRC": 1 if performance_1m > 0 else -1
        }
        
        # Calculate overall signal
        weights = {"MACD": 0.5, "PRC": 0.3, "RSI": 0.2, "SO": 0.4}
        overall_score = sum(indicator_scores[k] * weights[k] for k in indicator_scores)
        
        if overall_score > 0:
            overall_signal = "BULLISH"
        elif overall_score < 0:
            overall_signal = "BEARISH"
        else:
            overall_signal = "NEUTRAL"
        
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "performance_1m": round(performance_1m, 2),
            "performance_3m": round(performance_3m, 2),
            "performance_6m": round(performance_6m, 2),
            "adr_percentage": round(avg_adr_percentage, 2),
            "rsi": round(current_rsi, 2),
            "rsi_signal": rsi_signal,
            "macd": round(current_macd, 2),
            "macd_signal": round(current_macd_signal, 2),
            "stochastic_oscillator": round(current_stochastic, 2),
            "atr": round(current_atr, 2),
            "indicator_scores": indicator_scores,
            "overall_signal": overall_signal,
            "overall_score": round(overall_score, 2),
            "volume_avg_30d": int(recent_df['Volume'].mean()),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting data for {ticker}: {e}")
        return None

def screen_stocks(filters: Dict) -> List[Dict]:
    """Main screening function"""
    start_time = time.time()
    logger.info("=" * 80)
    logger.info("🚀 STOCK SCREENER STARTED")
    logger.info("=" * 80)
    
    sector = filters.get("sector", "tech")
    min_1m = filters.get("min_1m_performance", 10.0)
    min_3m = filters.get("min_3m_performance", 20.0)
    min_6m = filters.get("min_6m_performance", 30.0)
    # Handle None values for optional max filters
    max_1m = filters.get("max_1m_performance") if filters.get("max_1m_performance") is not None else 999999.0
    max_3m = filters.get("max_3m_performance") if filters.get("max_3m_performance") is not None else 999999.0
    max_6m = filters.get("max_6m_performance") if filters.get("max_6m_performance") is not None else 999999.0
    min_price = filters.get("min_price", 1.0)
    max_price = filters.get("max_price", 50.0)
    min_rsi = filters.get("min_rsi", 0.0)
    max_rsi = filters.get("max_rsi", 100.0)
    # Handle None values for optional ADR filters
    min_adr = filters.get("min_adr") if filters.get("min_adr") is not None else 0.0
    max_adr = filters.get("max_adr") if filters.get("max_adr") is not None else 999999.0
    rsi_signal = filters.get("rsi_signal", "all")
    sort_by = filters.get("sort_by", "adr")  # Default: sort by ADR
    sort_order = filters.get("sort_order", "desc")  # Default: descending
    limit = filters.get("limit", 50)
    
    logger.info(f"📊 Filters: sector={sector}, 1M: {min_1m}%-{max_1m}%, 3M: {min_3m}%-{max_3m}%, 6M: {min_6m}%-{max_6m}%")
    logger.info(f"💰 Price: ${min_price}-${max_price}, RSI: {min_rsi}-{max_rsi}, ADR: {min_adr}-{max_adr}%")
    logger.info(f"🔍 Signal: {rsi_signal}, Sort: {sort_by} ({sort_order}), Limit: {limit}")
    
    # Get tickers from universe, SIC CSV, or fallback to predefined sectors
    try:
        # Check if this is "universe" - use full ticker universe
        if sector == "universe":
            all_tickers = ticker_universe.get_ticker_symbols()
            if all_tickers:
                total = len(all_tickers)
                
                use_sample = filters.get("use_sample", False)
                sample_size = filters.get("sample_size", 3000)
                
                if use_sample:
                    sample_size = min(sample_size, total)
                    step = max(1, total // sample_size)
                    tickers = [all_tickers[i] for i in range(0, total, step)][:sample_size]
                    random.shuffle(tickers)
                    logger.info(f"📊 UNIVERSE MODE (SAMPLE): Screening {len(tickers)} stocks (stratified from {total} total)")
                else:
                    tickers = all_tickers
                    logger.info(f"📊 UNIVERSE MODE: Processing all {len(tickers)} stocks from universe")
                    logger.info(f"⏱️  Estimated time: ~60 minutes (first run), instant (if cached)")
            else:
                # Fallback to all predefined sectors
                tickers = []
                for sector_tickers in SECTOR_TICKERS.values():
                    tickers.extend(sector_tickers)
                tickers = list(dict.fromkeys(tickers))
                logger.warning(f"⚠️ Universe not available, using predefined sectors: {len(tickers)} stocks")
        
        # Check if predefined sector should use SIC-based sector (e.g., "tech" -> "tech_sic")
        elif sector in PREDEFINED_TO_SIC_MAPPING:
            sic_sector_key = PREDEFINED_TO_SIC_MAPPING[sector]
            sic_config = SIC_SECTOR_MAPPING[sic_sector_key]
            logger.info(f"📊 Sector '{sector}' mapped to SIC-based sector: {sic_config['display_name']}")
            
            # Try to load from SIC CSV file
            tickers = load_tickers_from_sic_csv(sic_config['csv_file'])
            
            # Fallback to predefined sector if SIC CSV is empty or not found
            if not tickers:
                logger.warning(f"⚠️  SIC CSV not available, falling back to predefined {sector} sector")
                tickers = SECTOR_TICKERS.get(sector, SECTOR_TICKERS["tech"])
                logger.info(f"📊 Using {len(tickers)} tickers from predefined {sector} sector")
            else:
                logger.info(f"✅ Loaded {len(tickers)} tickers from SIC-based {sic_config['display_name']} sector (mapped from '{sector}')")
        
        # Check if this is a SIC-based sector (e.g., "tech_sic")
        elif sector in SIC_SECTOR_MAPPING:
            sic_config = SIC_SECTOR_MAPPING[sector]
            logger.info(f"📊 Using SIC-based sector: {sic_config['display_name']}")
            
            # Try to load from SIC CSV file
            tickers = load_tickers_from_sic_csv(sic_config['csv_file'])
            
            # Fallback to predefined sector if SIC CSV is empty or not found
            if not tickers:
                logger.warning(f"⚠️  SIC CSV not available, falling back to predefined {sic_config['fallback']} sector")
                tickers = SECTOR_TICKERS.get(sic_config['fallback'], SECTOR_TICKERS["tech"])
                logger.info(f"📊 Using {len(tickers)} tickers from predefined {sic_config['fallback']} sector")
            else:
                logger.info(f"✅ Loaded {len(tickers)} tickers from SIC-based {sic_config['display_name']} sector")
        
        elif sector == "all" or sector not in SECTOR_TICKERS:
            # Try to get all tickers from universe
            all_tickers = ticker_universe.get_ticker_symbols()
            if all_tickers:
                # With unlimited API calls, we can use the full universe!
                # But start with a reasonable subset for performance
                total = len(all_tickers)
                
                # Default: Process ALL tickers to get true top performers by ADR
                # Only sample if explicitly requested (for faster testing/development)
                use_sample = filters.get("use_sample", False)
                sample_size = filters.get("sample_size", 3000)
                
                if use_sample:
                    # Use stratified sampling for faster results (testing/development only)
                    sample_size = min(sample_size, total)
                    step = max(1, total // sample_size)
                    tickers = [all_tickers[i] for i in range(0, total, step)][:sample_size]
                    random.shuffle(tickers)
                    logger.info(f"📊 SAMPLE MODE: Screening {len(tickers)} stocks (stratified from {total} total)")
                    logger.info(f"⚠️  Note: Sampling may miss top performers. Use default (no sampling) for accurate rankings.")
                else:
                    # Process all tickers to ensure accurate top X rankings
                    tickers = all_tickers
                    logger.info(f"📊 FULL SCAN MODE: Processing all {len(tickers)} stocks for accurate ranking")
                    logger.info(f"⏱️  Estimated time: ~60 minutes (first run with API calls), instant (if cached)")
                    logger.info(f"💡 Cache duration: {CACHE_DURATION_HOURS} hours - subsequent runs will be fast!")
            else:
                # Fallback to predefined sectors
                tickers = []
                for sector_tickers in SECTOR_TICKERS.values():
                    tickers.extend(sector_tickers)
                tickers = list(dict.fromkeys(tickers))
                logger.warning(f"⚠️ Screening {len(tickers)} stocks from predefined sectors (universe not available)...")
        else:
            # Use predefined sector
            tickers = SECTOR_TICKERS.get(sector, SECTOR_TICKERS["tech"])
            logger.info(f"📊 Screening {len(tickers)} {sector} stocks from predefined list...")
    except Exception as e:
        logger.error(f"⚠️ Error loading ticker universe: {e}")
        # Fallback to predefined sectors
        if sector == "universe":
            # Fallback to all predefined sectors if universe fails
            tickers = []
            for sector_tickers in SECTOR_TICKERS.values():
                tickers.extend(sector_tickers)
            tickers = list(dict.fromkeys(tickers))
            logger.warning(f"Using fallback: {len(tickers)} stocks from predefined sectors...")
        elif sector in PREDEFINED_TO_SIC_MAPPING:
            # Try SIC-based sector first, then fallback to predefined
            sic_sector_key = PREDEFINED_TO_SIC_MAPPING[sector]
            sic_config = SIC_SECTOR_MAPPING[sic_sector_key]
            tickers = load_tickers_from_sic_csv(sic_config['csv_file'])
            if not tickers:
                tickers = SECTOR_TICKERS.get(sector, SECTOR_TICKERS["tech"])
            logger.warning(f"Using fallback: {len(tickers)} stocks from {sector} sector...")
        elif sector in SIC_SECTOR_MAPPING:
            sic_config = SIC_SECTOR_MAPPING[sector]
            tickers = SECTOR_TICKERS.get(sic_config['fallback'], SECTOR_TICKERS["tech"])
            logger.warning(f"Using fallback: {len(tickers)} stocks from {sic_config['fallback']} sector...")
        elif sector == "all" or sector not in SECTOR_TICKERS:
            tickers = []
            for sector_tickers in SECTOR_TICKERS.values():
                tickers.extend(sector_tickers)
            tickers = list(dict.fromkeys(tickers))
        else:
            tickers = SECTOR_TICKERS.get(sector, SECTOR_TICKERS["tech"])
        logger.warning(f"Using fallback: {len(tickers)} stocks...")
    
    # Store original ticker list for completion tracking
    original_ticker_list = tickers.copy()
    original_ticker_count = len(original_ticker_list)
    filters_hash = get_filters_hash(filters)
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Try to load from cache first
    logger.info("=" * 80)
    logger.info("💾 LOADING CACHE")
    cached_data = load_cache()
    logger.info(f"✅ Loaded {len(cached_data)} stocks from cache")
    
    # Automatically check for existing checkpoint and resume if valid
    logger.info("=" * 80)
    logger.info("🔍 CHECKING FOR EXISTING PROGRESS")
    processed_tickers = set()
    checkpoint_stats = {"cached_count": 0, "fetched_count": 0, "failed_count": 0}
    
    checkpoint = load_checkpoint()
    if checkpoint:
        # Verify checkpoint matches current filters
        if checkpoint.get('filters_hash') == filters_hash:
            checkpoint_processed = set(checkpoint.get('processed_tickers', []))
            # Only count tickers that are in the current original list (avoid double counting from different runs)
            processed_tickers = set([t for t in checkpoint_processed if t in original_ticker_list])
            checkpoint_stats = checkpoint.get('stats', checkpoint_stats)
            batch_id = checkpoint.get('batch_id', batch_id)  # Use existing batch_id
            logger.info(f"📋 RESUMING: Found checkpoint with {len(checkpoint_processed)} tickers ({(len(processed_tickers))} in current universe)")
            logger.info(f"📊 Previous stats: Cached={checkpoint_stats['cached_count']}, "
                      f"Fetched={checkpoint_stats['fetched_count']}, Failed={checkpoint_stats['failed_count']}")
            
            # Filter out already processed tickers (only those in current universe)
            if processed_tickers:
                remaining_tickers = [t for t in tickers if t not in processed_tickers]
                logger.info(f"⏭️  Skipping {len(processed_tickers)} already processed tickers")
                logger.info(f"📊 Remaining to process: {len(remaining_tickers)} / {original_ticker_count}")
                tickers = remaining_tickers
        else:
            logger.info(f"⚠️  Checkpoint exists but filters don't match. Starting fresh.")
            logger.info(f"   (Old filters hash: {checkpoint.get('filters_hash')[:8]}, New: {filters_hash[:8]})")
            clear_checkpoint()
            processed_tickers = set()
    else:
        logger.info("🆕 No existing checkpoint - starting fresh")
    
    logger.info("=" * 80)
    logger.info("🔍 SCREENING STOCKS")
    logger.info(f"📊 Total tickers to process: {len(tickers)}")
    if processed_tickers:
        logger.info(f"🔧 Batch ID: {batch_id} | Resuming from checkpoint")
    
    # Track how many were processed at the start (from checkpoint, only in current universe)
    processed_at_start = len([t for t in processed_tickers if t in original_ticker_list])
    
    screened_stocks = []
    new_data = {}
    cached_count = checkpoint_stats.get("cached_count", 0)
    fetched_count = checkpoint_stats.get("fetched_count", 0)
    failed_count = checkpoint_stats.get("failed_count", 0)
    
    for i, ticker in enumerate(tickers):
        try:
            # Progress indicator every 10 stocks
            if i % 10 == 0 and i > 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                eta = (len(tickers) - i) / rate if rate > 0 else 0
                # Use processed_at_start (calculated once at start) + current progress (i)
                # This avoids double-counting since processed_tickers grows during the loop
                total_processed = processed_at_start + i
                logger.info(f"⚡ Progress: {i}/{len(tickers)} ({i/len(tickers)*100:.1f}%) | "
                          f"Total: {total_processed}/{original_ticker_count} | "
                          f"Cached: {cached_count} | Fetched: {fetched_count} | Failed: {failed_count} | "
                          f"ETA: {eta/60:.1f}min")
            
            # Check cache first
            if ticker in cached_data:
                stock_data = cached_data[ticker]
                cached_count += 1
            else:
                # Light rate limiting to avoid overwhelming the API
                # With unlimited calls, we can be more aggressive
                if i % 50 == 0 and i > 0:
                    time.sleep(0.1)  # Small pause every 50 requests
                
                stock_data = get_stock_performance_data(ticker)
                if stock_data:
                    new_data[ticker] = stock_data
                    fetched_count += 1
            
            if not stock_data:
                failed_count += 1
                # Mark as processed (even if failed) so we don't retry on resume
                processed_tickers.add(ticker)
                continue
            
            # Mark ticker as processed (always track for resume capability)
            processed_tickers.add(ticker)
            
            # Incremental cache save and checkpoint (automatic checkpointing)
            if (i + 1) % CHECKPOINT_INTERVAL == 0:
                # Merge new data into cache
                updated_cache = {**cached_data, **new_data}
                save_cache(updated_cache)
                cached_data = updated_cache  # Update local cache reference
                
                # Save checkpoint
                checkpoint_stats = {
                    "cached_count": cached_count,
                    "fetched_count": fetched_count,
                    "failed_count": failed_count
                }
                save_checkpoint(list(processed_tickers), filters_hash, batch_id, checkpoint_stats)
                logger.info(f"💾 Checkpoint saved: {len(processed_tickers)}/{original_ticker_count} tickers processed, "
                          f"{len(new_data)} new items cached")
                new_data = {}  # Clear new_data since it's now in cache
            
            # Apply filters
            rsi = stock_data.get("rsi", 50)
            rsi_signal_value = stock_data.get("rsi_signal", "NEUTRAL")
            
            # Check RSI signal filter
            rsi_signal_match = (rsi_signal == "all" or 
                              (rsi_signal == "oversold" and rsi_signal_value == "OVERSOLD") or
                              (rsi_signal == "overbought" and rsi_signal_value == "OVERBOUGHT") or
                              (rsi_signal == "neutral" and rsi_signal_value == "NEUTRAL"))
            
            adr = stock_data.get("adr_percentage", 0)
            
            # Apply all filters
            if (stock_data["current_price"] >= min_price and 
                stock_data["current_price"] <= max_price and
                stock_data["performance_1m"] >= min_1m and
                stock_data["performance_1m"] <= max_1m and
                stock_data["performance_3m"] >= min_3m and
                stock_data["performance_3m"] <= max_3m and
                stock_data["performance_6m"] >= min_6m and
                stock_data["performance_6m"] <= max_6m and
                rsi >= min_rsi and
                rsi <= max_rsi and
                adr >= min_adr and
                adr <= max_adr and
                rsi_signal_match):
                
                screened_stocks.append(stock_data)
                logger.info(f"✅ MATCH: {ticker} - {stock_data['performance_1m']}% 1M, "
                          f"{stock_data['performance_3m']}% 3M, {stock_data['performance_6m']}% 6M, "
                          f"RSI: {rsi:.1f} ({rsi_signal_value}), Signal: {stock_data['overall_signal']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing {ticker}: {e}")
            failed_count += 1
            continue
    
    # Final statistics
    # Count only tickers that are in the original list (to avoid double counting)
    total_processed = len([t for t in processed_tickers if t in original_ticker_list])
    processed_this_run = total_processed - processed_at_start
    logger.info("=" * 80)
    logger.info("📊 SCREENING COMPLETE")
    # Calculate how many were processed in THIS run
    processed_this_run = total_processed - processed_at_start
    logger.info(f"✅ Total processed in this run: {processed_this_run}")
    logger.info(f"📋 Total processed overall: {total_processed}/{original_ticker_count}")
    logger.info(f"📦 From cache: {cached_count}")
    logger.info(f"🔄 Newly fetched: {fetched_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"🎯 Matches found: {len(screened_stocks)}")
    
    # Save final cache and checkpoint
    if new_data:
        logger.info("💾 SAVING FINAL CACHE")
        # Merge new data with existing cache
        updated_cache = {**cached_data, **new_data}
        save_cache(updated_cache)
        logger.info(f"✅ Cached {len(updated_cache)} total stocks")
    
    # Save final checkpoint (always enabled)
    checkpoint_stats = {
        "cached_count": cached_count,
        "fetched_count": fetched_count,
        "failed_count": failed_count
    }
    save_checkpoint(list(processed_tickers), filters_hash, batch_id, checkpoint_stats)
    logger.info(f"💾 Final checkpoint saved: {total_processed}/{original_ticker_count} tickers processed")
    
    # Check if complete (all tickers processed)
    is_complete = len(processed_tickers) >= original_ticker_count
    if is_complete:
        logger.info("✅ COMPLETE - All tickers processed!")
        clear_checkpoint()
        logger.info("🗑️  Checkpoint cleared (processing complete)")
    else:
        logger.info(f"⏸️  IN PROGRESS - {original_ticker_count - total_processed} tickers remaining")
        logger.info(f"💡 Call again to resume from checkpoint")
    
    # Sort ALL filtered stocks by specified field and order
    # This ensures accurate rankings - we process all tickers, filter them all, 
    # sort them all, then return the top X (not just top X from a sample)
    sort_key_map = {
        "adr": "adr_percentage",
        "rsi": "rsi",
        "performance_1m": "performance_1m",
        "performance_3m": "performance_3m",
        "performance_6m": "performance_6m"
    }
    
    sort_key = sort_key_map.get(sort_by, "adr_percentage")
    reverse_order = (sort_order.lower() == "desc")
    
    # Ensure sort key exists in data, default to 0 if missing
    screened_stocks.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse_order)
    
    # Return top X results from the complete sorted list
    total_time = time.time() - start_time
    logger.info(f"⏱️  Total execution time: {total_time:.2f}s ({total_time/60:.2f}min)")
    logger.info(f"📊 Filtered matches: {len(screened_stocks)} | Returning top {min(limit, len(screened_stocks))} by ADR%")
    logger.info("=" * 80)
    
    return screened_stocks[:limit]

def get_market_snapshot_data(tickers: Optional[List[str]] = None, include_otc: bool = False) -> Dict:
    """
    Get a comprehensive market snapshot for the entire U.S. stock market
    
    Args:
        tickers: Optional list of specific tickers to get snapshots for.
                 If None or empty, returns all tickers (10,000+).
        include_otc: Whether to include OTC securities. Default is False.
    
    Returns:
        Dictionary containing formatted snapshot data with market-wide statistics
    """
    try:
        logger.info("=" * 80)
        logger.info("📊 FETCHING MARKET SNAPSHOT")
        
        if tickers:
            logger.info(f"📌 Requested tickers: {len(tickers)}")
        else:
            logger.info("🌐 Fetching complete market snapshot (10,000+ tickers)")
        
        if include_otc:
            logger.info("📈 Including OTC securities")
        
        # Call the Polygon API
        snapshot_data = get_market_snapshot(tickers=tickers, include_otc=include_otc)
        
        # Extract tickers from response
        tickers_data = snapshot_data.get("tickers", [])
        
        logger.info(f"✅ Received {len(tickers_data)} tickers")
        
        # Format the data for easier consumption
        formatted_tickers = []
        for ticker_data in tickers_data:
            day_data = ticker_data.get("day", {})
            prev_day_data = ticker_data.get("prevDay", {})
            last_trade = ticker_data.get("lastTrade", {})
            
            formatted_ticker = {
                "ticker": ticker_data.get("ticker"),
                "current_price": day_data.get("c", 0),
                "open": day_data.get("o", 0),
                "high": day_data.get("h", 0),
                "low": day_data.get("l", 0),
                "close": day_data.get("c", 0),
                "volume": day_data.get("v", 0),
                "vwap": day_data.get("vw", 0),  # Volume-weighted average price
                "todays_change": ticker_data.get("todaysChange", 0),
                "todays_change_perc": ticker_data.get("todaysChangePerc", 0),
                "prev_day": {
                    "close": prev_day_data.get("c", 0),
                    "high": prev_day_data.get("h", 0),
                    "low": prev_day_data.get("l", 0),
                    "open": prev_day_data.get("o", 0),
                    "volume": prev_day_data.get("v", 0)
                },
                "last_trade": {
                    "price": last_trade.get("p", 0),
                    "size": last_trade.get("s", 0),
                    "timestamp": last_trade.get("t", 0)
                },
                "updated": ticker_data.get("updated", 0)
            }
            
            formatted_tickers.append(formatted_ticker)
        
        # Calculate market-wide statistics
        if formatted_tickers:
            total_volume = sum(t["volume"] for t in formatted_tickers)
            gainers = sum(1 for t in formatted_tickers if t["todays_change_perc"] > 0)
            losers = sum(1 for t in formatted_tickers if t["todays_change_perc"] < 0)
            unchanged = len(formatted_tickers) - gainers - losers
            
            # Find top movers
            sorted_by_change = sorted(formatted_tickers, 
                                    key=lambda x: x["todays_change_perc"], 
                                    reverse=True)
            
            market_stats = {
                "total_tickers": len(formatted_tickers),
                "total_volume": total_volume,
                "gainers": gainers,
                "losers": losers,
                "unchanged": unchanged,
                "top_gainers": [
                    {
                        "ticker": t["ticker"],
                        "change_perc": round(t["todays_change_perc"], 2),
                        "price": t["current_price"],
                        "volume": t["volume"]
                    }
                    for t in sorted_by_change[:10]
                ],
                "top_losers": [
                    {
                        "ticker": t["ticker"],
                        "change_perc": round(t["todays_change_perc"], 2),
                        "price": t["current_price"],
                        "volume": t["volume"]
                    }
                    for t in sorted_by_change[-10:][::-1]
                ]
            }
        else:
            market_stats = {
                "total_tickers": 0,
                "total_volume": 0,
                "gainers": 0,
                "losers": 0,
                "unchanged": 0,
                "top_gainers": [],
                "top_losers": []
            }
        
        logger.info(f"📈 Gainers: {market_stats['gainers']}, Losers: {market_stats['losers']}, Unchanged: {market_stats['unchanged']}")
        logger.info(f"📊 Total Volume: {market_stats['total_volume']:,}")
        logger.info("=" * 80)
        
        return {
            "status": snapshot_data.get("status", "OK"),
            "count": len(formatted_tickers),
            "market_statistics": market_stats,
            "tickers": formatted_tickers
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching market snapshot: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "count": 0,
            "market_statistics": {},
            "tickers": []
        }

def get_available_sectors() -> Dict:
    """
    Get list of available sectors for frontend dropdown.
    Returns only: Universe, All, and SIC-based sectors (Technology/AI, Energy, Healthcare/Biotech)
    """
    sectors_info = {}
    
    # Add "universe" option (uses full ticker universe)
    try:
        all_universe_tickers = ticker_universe.get_ticker_symbols()
        universe_count = len(all_universe_tickers) if all_universe_tickers else 0
    except:
        universe_count = 0
    
    sectors_info["universe"] = {
        "name": "Universe",
        "ticker_count": universe_count,
        "tickers": all_universe_tickers[:20] if all_universe_tickers else [],
        "type": "universe",
        "value": "universe"  # Backend value to send
    }
    
    # Add SIC-based sectors only (these are the ones we want in the dropdown)
    for sector_key, sic_config in SIC_SECTOR_MAPPING.items():
        # Try to load from CSV to get accurate count
        tickers = load_tickers_from_sic_csv(sic_config['csv_file'])
        
        if not tickers:
            # Fallback to predefined sector count
            fallback_tickers = SECTOR_TICKERS.get(sic_config['fallback'], [])
            ticker_count = len(fallback_tickers)
            example_tickers = fallback_tickers[:10]
            available = False
        else:
            ticker_count = len(tickers)
            example_tickers = tickers[:10]
            available = True
        
        sectors_info[sector_key] = {
            "name": sic_config['display_name'],  # Human-readable name for frontend
            "ticker_count": ticker_count,
            "tickers": example_tickers,
            "type": "sic_based",
            "available": available,
            "csv_file": sic_config['csv_file'],
            "value": sector_key  # Backend value to send (e.g., "tech_sic")
        }
    
    # Add "all" option (uses all predefined sectors combined)
    all_tickers = []
    for tickers in SECTOR_TICKERS.values():
        all_tickers.extend(tickers)
    all_tickers = list(dict.fromkeys(all_tickers))  # Remove duplicates
    
    sectors_info["all"] = {
        "name": "All Sectors",
        "ticker_count": len(all_tickers),
        "tickers": all_tickers[:20],  # Show first 20 tickers as examples
        "type": "all",
        "value": "all"  # Backend value to send
    }
    
    return sectors_info

def get_sector_performance_summary(sector: str) -> Dict:
    """Get summary statistics for a sector"""
    tickers = SECTOR_TICKERS.get(sector, [])
    if not tickers:
        return {"error": "Invalid sector"}
    
    total_stocks = len(tickers)
    screened_count = 0
    avg_performance_1m = 0
    avg_performance_3m = 0
    avg_performance_6m = 0
    
    for ticker in tickers[:20]:  # Sample first 20 for summary
        data = get_stock_performance_data(ticker)
        if data:
            screened_count += 1
            avg_performance_1m += data["performance_1m"]
            avg_performance_3m += data["performance_3m"]
            avg_performance_6m += data["performance_6m"]
    
    if screened_count > 0:
        avg_performance_1m /= screened_count
        avg_performance_3m /= screened_count
        avg_performance_6m /= screened_count
    
    return {
        "sector": sector,
        "total_stocks": total_stocks,
        "sampled_stocks": screened_count,
        "avg_performance_1m": round(avg_performance_1m, 2),
        "avg_performance_3m": round(avg_performance_3m, 2),
        "avg_performance_6m": round(avg_performance_6m, 2)
    }
