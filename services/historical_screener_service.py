# services/historical_screener_service.py

import pandas as pd
import logging
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from utils.polygon_client import get_price_history_at_date
from services.ticker_universe_service import ticker_universe
from services.backtest_session_cache import (
    create_session, get_session, find_session_by_date,
    update_session, add_trade_to_session
)

# Import calculation functions from stock_screener_service
from services.stock_screener_service import (
    calculate_performance_percentage,
    calculate_adr_percentage,
    calculate_rsi,
    calculate_macd,
    calculate_stochastic_oscillator,
    calculate_atr,
    SECTOR_TICKERS,
    SIC_SECTOR_MAPPING,
    PREDEFINED_TO_SIC_MAPPING,
    load_tickers_from_sic_csv
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting configuration
# Free tier: ~5 calls/minute | Pro tier: ~200 calls/minute | Advanced: ~500 calls/minute
DEFAULT_RATE_LIMIT_CALLS_PER_MINUTE = 5  # Conservative default
PRO_TIER_RATE_LIMIT = 200  # Pro tier allows much higher rates


def get_historical_stock_data(ticker: str, reference_date: str, lookback_days: int = 180) -> Optional[Dict]:
    """
    Get stock performance data calculated using only data up to the reference date.
    This simulates what the data would have looked like at that point in time.
    
    Args:
        ticker: Stock ticker symbol
        reference_date: Reference date in YYYY-MM-DD format
        lookback_days: Number of days to look back from reference_date
    
    Returns:
        Dictionary with stock data as it would have appeared at reference_date, or None if insufficient data
    """
    try:
        # Get price history up to (and including) reference_date
        logger.debug(f"   Fetching data for {ticker} (reference: {reference_date}, lookback: {lookback_days} days)")
        bars = get_price_history_at_date(ticker, reference_date, days_back=lookback_days)
        
        if not bars or len(bars) < 30:
            logger.debug(f"   ⚠️  Insufficient data for {ticker}: {len(bars) if bars else 0} bars (need 30+)")
            return None
        
        logger.debug(f"   ✅ Got {len(bars)} bars for {ticker}")
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        df['Date'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        # Get "current" price (most recent close up to reference_date)
        current_price = df['Close'].iloc[-1]
        
        # Calculate performance periods using only data up to reference_date
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
        
        # Calculate ADR% (Average Daily Range) for last 30 days available
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
        
        # Calculate indicator scores
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
            "last_updated": reference_date  # Use reference date, not current date
        }
        
    except Exception as e:
        logger.warning(f"Error getting historical data for {ticker} at {reference_date}: {e}")
        return None


def get_historical_rankings(
    reference_date: str,
    top_n: int = 50,
    sector: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_adr: Optional[float] = None,
    max_adr: Optional[float] = None,
    # Performance filters (matching regular scanner)
    min_1m_performance: Optional[float] = None,
    max_1m_performance: Optional[float] = None,
    min_3m_performance: Optional[float] = None,
    max_3m_performance: Optional[float] = None,
    min_6m_performance: Optional[float] = None,
    max_6m_performance: Optional[float] = None,
    sort_by: str = 'adr',
    sort_order: str = 'desc',
    lookback_days: int = 180,
    # Optimization parameters
    use_sample: bool = False,
    sample_size: int = 1000,
    max_universe_size: Optional[int] = None,
    enable_rate_limiting: bool = True,
    # Parallel processing parameters
    max_workers: int = 5,  # Number of concurrent threads (default: 5 for Pro tier)
    rate_limit_per_minute: int = PRO_TIER_RATE_LIMIT  # API rate limit (default: 200 for Pro tier)
) -> List[Dict]:
    """
    Get historical stock rankings as they would have appeared at the reference_date.
    
    Args:
        reference_date: Reference date in YYYY-MM-DD format
        top_n: Number of top stocks to return
        sector: Optional sector filter (use predefined sectors like 'tech', 'finance', etc.)
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        min_adr: Optional minimum ADR filter
        max_adr: Optional maximum ADR filter
        min_1m_performance: Optional minimum 1-month performance filter (%)
        max_1m_performance: Optional maximum 1-month performance filter (%)
        min_3m_performance: Optional minimum 3-month performance filter (%)
        max_3m_performance: Optional maximum 3-month performance filter (%)
        min_6m_performance: Optional minimum 6-month performance filter (%)
        max_6m_performance: Optional maximum 6-month performance filter (%)
        sort_by: Field to sort by ('adr', 'rsi', 'performance_1m', etc.)
        sort_order: 'asc' or 'desc'
        lookback_days: Days to look back for calculations
        use_sample: If True, use sampling for faster results (trades accuracy for speed)
        sample_size: Number of stocks to sample if use_sample=True
        max_universe_size: Maximum number of stocks to process (None = no limit)
        enable_rate_limiting: If True, add delays between API calls to respect rate limits
        max_workers: Number of concurrent worker threads (default: 5, set higher for Pro tier)
        rate_limit_per_minute: API rate limit per minute (default: 200 for Pro tier)
    
    Returns:
        List of stock data dictionaries, ranked and filtered
    """
    logger.info(f"📊 Getting historical rankings for {reference_date}")
    logger.info(f"🔍 Filters: 1M: {min_1m_performance}%-{max_1m_performance}%, "
               f"3M: {min_3m_performance}%-{max_3m_performance}%, "
               f"6M: {min_6m_performance}%-{max_6m_performance}%")
    start_time = time.time()
    
    # Create session early (before processing starts) so it's available even if request times out
    filters_dict = {
        'sector': sector,
        'min_price': min_price,
        'max_price': max_price,
        'min_adr': min_adr,
        'max_adr': max_adr,
        'min_1m_performance': min_1m_performance,
        'max_1m_performance': max_1m_performance,
        'min_3m_performance': min_3m_performance,
        'max_3m_performance': max_3m_performance,
        'min_6m_performance': min_6m_performance,
        'max_6m_performance': max_6m_performance,
        'sort_by': sort_by,
        'sort_order': sort_order
    }
    # Remove None values
    filters_dict = {k: v for k, v in filters_dict.items() if v is not None}
    
    # Initialize session_id (will be set when session is created)
    session_id = None
    try:
        # Create session with empty rankings (will be updated when processing completes)
        session_id = create_session(
            reference_date=reference_date,
            filters=filters_dict,
            historical_rankings=[]  # Empty initially, will be updated
        )
        logger.info(f"💾 Created session {session_id} (processing will update it when complete)")
    except Exception as e:
        logger.warning(f"⚠️  Failed to create session early: {e}")
        # Continue anyway - we'll try to create it at the end
    
    # Get ticker universe
    try:
        all_tickers = ticker_universe.get_ticker_symbols()
        if not all_tickers or len(all_tickers) == 0:
            logger.error("❌ No tickers found in universe. Make sure data/us_stock_universe.csv exists.")
            raise ValueError("No tickers available in universe. Please run scripts/fetch_ticker_universe.py to create the universe file.")
    except Exception as e:
        logger.error(f"❌ Error getting ticker universe: {e}")
        raise ValueError(f"Failed to load ticker universe: {str(e)}")
    
    # OPTIMIZATION 1: Filter by sector if provided
    # Support for: universe, all, predefined sectors (tech, energy, bio, finance), SIC sectors (tech_sic, energy_sic, healthcare_sic)
    if not sector or sector.lower() == "all":
        ticker_list = all_tickers
        logger.info(f"📊 Using full universe: {len(ticker_list)} stocks")
    elif sector.lower() == "universe":
        ticker_list = all_tickers
        logger.info(f"📊 Using full universe: {len(ticker_list)} stocks")
    elif sector.lower() in PREDEFINED_TO_SIC_MAPPING:
        # Predefined sector (tech, energy, bio) -> use SIC-based sector
        sic_sector_key = PREDEFINED_TO_SIC_MAPPING[sector.lower()]
        sic_config = SIC_SECTOR_MAPPING[sic_sector_key]
        logger.info(f"📊 Sector '{sector}' mapped to SIC-based sector: {sic_config['display_name']}")
        
        # Try to load from SIC CSV file
        ticker_list = load_tickers_from_sic_csv(sic_config['csv_file'])
        
        # Fallback to predefined sector if SIC CSV is empty or not found
        if not ticker_list:
            logger.warning(f"⚠️  SIC CSV not available, falling back to predefined {sector} sector")
            ticker_list = SECTOR_TICKERS.get(sector.lower(), all_tickers)
            logger.info(f"📊 Using {len(ticker_list)} tickers from predefined {sector} sector")
        else:
            logger.info(f"✅ Loaded {len(ticker_list)} tickers from SIC-based {sic_config['display_name']} sector (mapped from '{sector}')")
    elif sector.lower() in SIC_SECTOR_MAPPING:
        # Direct SIC sector (tech_sic, energy_sic, healthcare_sic)
        sic_config = SIC_SECTOR_MAPPING[sector.lower()]
        logger.info(f"📊 Using SIC-based sector: {sic_config['display_name']}")
        
        # Try to load from SIC CSV file
        ticker_list = load_tickers_from_sic_csv(sic_config['csv_file'])
        
        # Fallback to predefined sector if SIC CSV is empty or not found
        if not ticker_list:
            logger.warning(f"⚠️  SIC CSV not available, falling back to predefined {sic_config['fallback']} sector")
            ticker_list = SECTOR_TICKERS.get(sic_config['fallback'], all_tickers)
            logger.info(f"📊 Using {len(ticker_list)} tickers from predefined {sic_config['fallback']} sector")
        else:
            logger.info(f"✅ Loaded {len(ticker_list)} tickers from SIC-based {sic_config['display_name']} sector")
    elif sector.lower() in SECTOR_TICKERS:
        # Predefined sector (tech, finance, energy, bio) - use predefined list
        ticker_list = SECTOR_TICKERS[sector.lower()]
        logger.info(f"📊 Sector filter applied: {sector} ({len(ticker_list)} stocks from predefined list)")
    else:
        logger.warning(f"⚠️  Unknown sector '{sector}', using full universe")
        ticker_list = all_tickers
    
    if not ticker_list or len(ticker_list) == 0:
        logger.error("❌ No tickers to process after filtering")
        raise ValueError("No tickers available to process. Check sector filter or ticker universe.")
    
    # OPTIMIZATION 2: Apply max universe size limit
    if max_universe_size and len(ticker_list) > max_universe_size:
        ticker_list = ticker_list[:max_universe_size]
        logger.info(f"📊 Limited universe to {max_universe_size} stocks (first {max_universe_size} from list)")
    
    # OPTIMIZATION 3: Apply sampling for faster results
    if use_sample and len(ticker_list) > sample_size:
        # Stratified sampling: take evenly spaced stocks
        step = max(1, len(ticker_list) // sample_size)
        sampled_tickers = [ticker_list[i] for i in range(0, len(ticker_list), step)][:sample_size]
        # Shuffle to avoid bias
        random.shuffle(sampled_tickers)
        ticker_list = sampled_tickers
        logger.info(f"📊 SAMPLING MODE: Processing {len(ticker_list)} stocks (sampled from {len(all_tickers)} total)")
        logger.info(f"⚠️  Note: Sampling trades accuracy for speed. Disable for accurate rankings.")
    else:
        logger.info(f"📊 FULL SCAN MODE: Processing {len(ticker_list)} stocks")
    
    results = []
    results_lock = Lock()  # Thread-safe lock for results list
    total_tickers = len(ticker_list)
    processed_count = 0
    processed_lock = Lock()  # Thread-safe lock for progress counter
    
    # Calculate rate limiting
    if enable_rate_limiting:
        rate_limit_delay = 60.0 / rate_limit_per_minute
        # Adjust max_workers to respect rate limit (don't exceed what rate limit allows)
        # With rate_limit_per_minute = 200, we can do ~3.3 calls/second
        # max_workers should be reasonable (5-10 workers is good for Pro tier)
        effective_workers = min(max_workers, max(1, rate_limit_per_minute // 20))  # Conservative: divide by 20
        estimated_time = (total_tickers / effective_workers) * rate_limit_delay / 60
        logger.info(f"🚀 Processing {total_tickers} tickers with {effective_workers} concurrent workers")
        logger.info(f"⚡ Rate limit: {rate_limit_per_minute} calls/minute (~{rate_limit_delay:.2f}s between calls)")
        logger.info(f"⏱️  Estimated time: ~{estimated_time:.1f} minutes (parallel processing)")
    else:
        effective_workers = max_workers
        estimated_time = (total_tickers / effective_workers) * 0.5 / 60
        logger.info(f"🚀 Processing {total_tickers} tickers with {effective_workers} concurrent workers (no rate limiting)")
        logger.info(f"⏱️  Estimated time: ~{estimated_time:.1f} minutes (parallel processing)")
        rate_limit_delay = 0
    
    # Thread-safe rate limiter
    class RateLimiter:
        def __init__(self, calls_per_minute: int):
            self.calls_per_minute = calls_per_minute
            self.min_interval = 60.0 / calls_per_minute if calls_per_minute > 0 else 0
            self.last_call_times = []
            self.lock = Lock()
        
        def wait_if_needed(self):
            """Wait if necessary to respect rate limit"""
            if not enable_rate_limiting or self.min_interval == 0:
                return
            
            with self.lock:
                now = time.time()
                # Remove old call times (older than 1 minute)
                self.last_call_times = [t for t in self.last_call_times if now - t < 60.0]
                
                # If we've hit the rate limit, wait
                if len(self.last_call_times) >= self.calls_per_minute:
                    oldest_call = min(self.last_call_times)
                    wait_time = 60.0 - (now - oldest_call) + 0.1  # Small buffer
                    if wait_time > 0:
                        time.sleep(wait_time)
                        # Clean up again after waiting
                        now = time.time()
                        self.last_call_times = [t for t in self.last_call_times if now - t < 60.0]
                
                # Record this call
                self.last_call_times.append(time.time())
    
    rate_limiter = RateLimiter(rate_limit_per_minute) if enable_rate_limiting else None
    
    # Worker progress tracking
    worker_progress = {}  # {worker_id: {'completed': count, 'start_time': time}}
    worker_progress_lock = Lock()
    
    def process_ticker(ticker: str) -> Optional[Dict]:
        """Process a single ticker (used by thread pool)"""
        worker_id = threading.current_thread().name
        filter_reason = None
        
        # Initialize worker progress tracking
        with worker_progress_lock:
            if worker_id not in worker_progress:
                worker_progress[worker_id] = {
                    'completed': 0,
                    'start_time': time.time()
                }
        
        try:
            # Rate limiting (thread-safe)
            if rate_limiter:
                rate_limiter.wait_if_needed()
            
            stock_data = get_historical_stock_data(ticker, reference_date, lookback_days)
            
            if not stock_data:
                filter_reason = "no data"
                return None
            
            # Apply filters
            if min_price and stock_data['current_price'] < min_price:
                filter_reason = "price < min"
            elif max_price and stock_data['current_price'] > max_price:
                filter_reason = "price > max"
            elif min_adr and stock_data['adr_percentage'] < min_adr:
                filter_reason = "ADR < min"
            elif max_adr and stock_data['adr_percentage'] > max_adr:
                filter_reason = "ADR > max"
            elif min_1m_performance is not None and stock_data.get('performance_1m', 0) < min_1m_performance:
                filter_reason = "1m perf < min"
            elif max_1m_performance is not None and stock_data.get('performance_1m', 0) > max_1m_performance:
                filter_reason = "1m perf > max"
            elif min_3m_performance is not None and stock_data.get('performance_3m', 0) < min_3m_performance:
                filter_reason = "3m perf < min"
            elif max_3m_performance is not None and stock_data.get('performance_3m', 0) > max_3m_performance:
                filter_reason = "3m perf > max"
            elif min_6m_performance is not None and stock_data.get('performance_6m', 0) < min_6m_performance:
                filter_reason = "6m perf < min"
            elif max_6m_performance is not None and stock_data.get('performance_6m', 0) > max_6m_performance:
                filter_reason = "6m perf > max"
            
            if filter_reason:
                return None
            else:
                return stock_data
            
        except Exception as e:
            logger.warning(f"❌ [{worker_id}] Error processing {ticker}: {e}")
            return None
        finally:
            # Update worker progress
            with worker_progress_lock:
                if worker_id in worker_progress:
                    worker_progress[worker_id]['completed'] += 1
    
    # Process tickers in parallel using ThreadPoolExecutor
    logger.info(f"🔄 Starting parallel processing with {effective_workers} workers...")
    last_log_time = time.time()
    log_interval = 10  # Log every 10 seconds
    last_worker_status_time = time.time()
    worker_status_interval = 15  # Report worker status every 15 seconds
    
    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        # Submit all tasks
        future_to_ticker = {executor.submit(process_ticker, ticker): ticker for ticker in ticker_list}
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            
            try:
                stock_data = future.result()
                if stock_data:
                    with results_lock:
                        results.append(stock_data)
            except Exception as e:
                logger.warning(f"⚠️  Exception processing {ticker}: {e}")
            
            # Update progress counter
            with processed_lock:
                processed_count += 1
                current_progress = processed_count
                
                # Overall progress logging
                current_time = time.time()
                if current_time - last_log_time >= log_interval or current_progress % 50 == 0 or current_progress == total_tickers:
                    elapsed = current_time - start_time
                    rate = current_progress / elapsed if elapsed > 0 else 0
                    remaining = (total_tickers - current_progress) / rate if rate > 0 else 0
                    
                    logger.info(f"📈 Overall Progress: {current_progress}/{total_tickers} ({100*current_progress/total_tickers:.1f}%) | "
                               f"Found: {len(results)} matches | "
                               f"Rate: {rate:.1f} tickers/sec | "
                               f"Elapsed: {elapsed/60:.1f}m | "
                               f"Remaining: ~{remaining/60:.1f}m")
                    last_log_time = current_time
                
                # Worker status reporting (every 15 seconds)
                if current_time - last_worker_status_time >= worker_status_interval:
                    with worker_progress_lock:
                        status_lines = []
                        total_worker_completed = sum(p['completed'] for p in worker_progress.values())
                        for worker_id, progress in sorted(worker_progress.items()):
                            if total_worker_completed > 0:
                                # Show each worker's contribution as percentage of total work done
                                worker_pct = 100 * progress['completed'] / total_worker_completed
                                elapsed_worker = current_time - progress['start_time']
                                worker_rate = progress['completed'] / elapsed_worker if elapsed_worker > 0 else 0
                                status_lines.append(f"{worker_id}: {worker_pct:.1f}% ({progress['completed']} tasks, {worker_rate:.1f}/s)")
                            else:
                                elapsed_worker = current_time - progress['start_time']
                                status_lines.append(f"{worker_id}: 0% (0 tasks, {elapsed_worker:.0f}s)")
                        
                        if status_lines:
                            logger.info(f"👷 Worker Status: {' | '.join(status_lines)}")
                    last_worker_status_time = current_time
    
    elapsed_time = time.time() - start_time
    logger.info(f"✅ Processed {total_tickers} tickers in {elapsed_time/60:.1f} minutes using {effective_workers} workers")
    logger.info(f"📊 Found {len(results)} stocks matching filters")
    if elapsed_time > 0:
        logger.info(f"⚡ Average rate: {total_tickers / elapsed_time:.2f} tickers/second")
    
    # Sort results
    reverse = sort_order.lower() == 'desc'
    sort_key_map = {
        'adr': 'adr_percentage',
        'rsi': 'rsi',
        'performance_1m': 'performance_1m',
        'performance_3m': 'performance_3m',
        'performance_6m': 'performance_6m',
        'overall_score': 'overall_score'
    }
    
    sort_key = sort_key_map.get(sort_by, 'adr_percentage')
    results.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)
    
    logger.info(f"🎯 Returning top {min(top_n, len(results))} stocks (sorted by {sort_by} {sort_order})")
    
    final_results = results[:top_n]
    
    # Update session cache with final results
    try:
        if session_id:
            # Update existing session with final rankings
            update_session(
                session_id=session_id,
                historical_rankings=final_results
            )
            logger.info(f"💾 Updated session {session_id} with {len(final_results)} rankings")
        else:
            # Fallback: create session now if it wasn't created earlier
            session_id = create_session(
                reference_date=reference_date,
                filters=filters_dict,
                historical_rankings=final_results
            )
            logger.info(f"💾 Created session {session_id} with {len(final_results)} rankings")
    except Exception as e:
        logger.warning(f"⚠️  Failed to update session: {e}")
        # Don't fail the request if session saving fails
    
    # Return top N results along with session_id
    # Note: Session is saved to disk, so even if request times out, it's available via session_id
    return {
        'rankings': final_results,
        'session_id': session_id
    }

