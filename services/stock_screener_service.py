# services/stock_screener_service.py

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.polygon_client import get_price_history
import pandas as pd
import json
import os

# Import ticker universe service
from services.ticker_universe_service import ticker_universe

# Cache configuration
CACHE_DURATION_HOURS = 1  # Cache for 1 hour
CACHE_FILE = "cache/stock_screener_cache.json"

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
    sector = filters.get("sector", "tech")
    min_1m = filters.get("min_1m_performance", 10.0)
    min_3m = filters.get("min_3m_performance", 20.0)
    min_6m = filters.get("min_6m_performance", 30.0)
    min_price = filters.get("min_price", 1.0)
    max_price = filters.get("max_price", 50.0)
    min_rsi = filters.get("min_rsi", 0.0)
    max_rsi = filters.get("max_rsi", 100.0)
    rsi_signal = filters.get("rsi_signal", "all")
    limit = filters.get("limit", 50)
    
    # Get tickers from universe or fallback to predefined sectors
    try:
        if sector == "all" or sector not in SECTOR_TICKERS:
            # Try to get all tickers from universe
            all_tickers = ticker_universe.get_ticker_symbols()
            if all_tickers:
                # Use more stocks from universe for better screening
                tickers = all_tickers[:2000]  # Increased from 500 to 2000 for better coverage
                print(f"📊 Screening {len(tickers)} stocks from universe (using first 2000 for performance)...")
            else:
                # Fallback to predefined sectors
                tickers = []
                for sector_tickers in SECTOR_TICKERS.values():
                    tickers.extend(sector_tickers)
                tickers = list(dict.fromkeys(tickers))
                print(f"⚠️ Screening {len(tickers)} stocks from predefined sectors (universe not available)...")
        else:
            # Use predefined sector
            tickers = SECTOR_TICKERS.get(sector, SECTOR_TICKERS["tech"])
            print(f"Screening {len(tickers)} {sector} stocks from predefined list...")
    except Exception as e:
        print(f"⚠️ Error loading ticker universe: {e}")
        # Fallback to predefined sectors
        if sector == "all" or sector not in SECTOR_TICKERS:
            tickers = []
            for sector_tickers in SECTOR_TICKERS.values():
                tickers.extend(sector_tickers)
            tickers = list(dict.fromkeys(tickers))
        else:
            tickers = SECTOR_TICKERS.get(sector, SECTOR_TICKERS["tech"])
        print(f"Using fallback: {len(tickers)} stocks...")
    
    # Try to load from cache first
    cached_data = load_cache()
    screened_stocks = []
    new_data = {}
    
    for i, ticker in enumerate(tickers):
        try:
            # Check cache first
            if ticker in cached_data:
                stock_data = cached_data[ticker]
                print(f"📦 Using cached data for {ticker}")
            else:
                # Rate limiting - pause every 10 requests
                if i % 10 == 0 and i > 0:
                    time.sleep(0.5)
                
                stock_data = get_stock_performance_data(ticker)
                if stock_data:
                    new_data[ticker] = stock_data
                    print(f"🔄 Fetched fresh data for {ticker}")
            
            if not stock_data:
                continue
            
            # Apply filters
            rsi = stock_data.get("rsi", 50)
            rsi_signal_value = stock_data.get("rsi_signal", "NEUTRAL")
            
            # Check RSI signal filter
            rsi_signal_match = (rsi_signal == "all" or 
                              (rsi_signal == "oversold" and rsi_signal_value == "OVERSOLD") or
                              (rsi_signal == "overbought" and rsi_signal_value == "OVERBOUGHT") or
                              (rsi_signal == "neutral" and rsi_signal_value == "NEUTRAL"))
            
            if (stock_data["current_price"] >= min_price and 
                stock_data["current_price"] <= max_price and
                stock_data["performance_1m"] >= min_1m and
                stock_data["performance_3m"] >= min_3m and
                stock_data["performance_6m"] >= min_6m and
                rsi >= min_rsi and
                rsi <= max_rsi and
                rsi_signal_match):
                
                screened_stocks.append(stock_data)
                print(f"✅ {ticker}: {stock_data['performance_1m']}% 1M, {stock_data['performance_3m']}% 3M, {stock_data['performance_6m']}% 6M, RSI: {rsi:.1f} ({rsi_signal_value}), Signal: {stock_data['overall_signal']}")
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue
    
    # Save new data to cache
    if new_data:
        # Merge new data with existing cache
        updated_cache = {**cached_data, **new_data}
        save_cache(updated_cache)
    
    # Sort by ADR% (highest first)
    screened_stocks.sort(key=lambda x: x["adr_percentage"], reverse=True)
    
    # Limit results
    return screened_stocks[:limit]

def get_available_sectors() -> Dict:
    """Get list of available sectors and their ticker counts"""
    sectors_info = {}
    for sector, tickers in SECTOR_TICKERS.items():
        sectors_info[sector] = {
            "name": sector.title(),
            "ticker_count": len(tickers),
            "tickers": tickers[:10]  # Show first 10 tickers as examples
        }
    
    # Add "all" option
    all_tickers = []
    for tickers in SECTOR_TICKERS.values():
        all_tickers.extend(tickers)
    all_tickers = list(dict.fromkeys(all_tickers))  # Remove duplicates
    
    sectors_info["all"] = {
        "name": "All Sectors",
        "ticker_count": len(all_tickers),
        "tickers": all_tickers[:20]  # Show first 20 tickers as examples
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
