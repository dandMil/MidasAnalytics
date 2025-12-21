# services/backtest_trade_simulator.py

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from utils.polygon_client import get_forward_price_history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simulate_trade(
    ticker: str,
    entry_date: str,  # YYYY-MM-DD format
    entry_price: float,
    quantity: int,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    exit_date: Optional[str] = None,  # YYYY-MM-DD format, optional forced exit
    max_hold_days: Optional[int] = None
) -> Dict:
    """
    Simulate a trade and track performance forward from entry date.
    
    Args:
        ticker: Stock ticker symbol
        entry_date: Entry date in YYYY-MM-DD format
        entry_price: Entry price per share
        quantity: Number of shares
        stop_loss: Optional stop loss price
        take_profit: Optional take profit price
        exit_date: Optional forced exit date (YYYY-MM-DD)
        max_hold_days: Optional maximum holding period in days
    
    Returns:
        Dictionary with trade simulation results
    """
    import time
    start_time = time.time()
    
    logger.info(f"🔄 Starting trade simulation for {ticker}")
    logger.info(f"   Entry Date: {entry_date}, Entry Price: ${entry_price:.2f}, Quantity: {quantity}")
    logger.info(f"   Stop Loss: ${stop_loss:.2f}" if stop_loss else "   Stop Loss: None")
    logger.info(f"   Take Profit: ${take_profit:.2f}" if take_profit else "   Take Profit: None")
    logger.info(f"   Max Hold Days: {max_hold_days}" if max_hold_days else "   Max Hold Days: None")
    
    try:
        # Calculate end date for data fetching
        if exit_date:
            end_date = exit_date
            logger.info(f"   Using forced exit date: {end_date}")
        elif max_hold_days:
            entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
            end_date_obj = entry_date_obj + timedelta(days=max_hold_days)
            end_date = end_date_obj.strftime("%Y-%m-%d")
            logger.info(f"   Calculated end date from max_hold_days: {end_date} ({max_hold_days} days)")
        else:
            # Default to 90 days forward if no exit criteria
            entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
            end_date_obj = entry_date_obj + timedelta(days=90)
            end_date = end_date_obj.strftime("%Y-%m-%d")
            logger.info(f"   Using default 90-day lookahead: {end_date}")
        
        # Get forward price history (from entry_date forward)
        logger.info(f"📡 Fetching price history from {entry_date} to {end_date}...")
        fetch_start = time.time()
        bars = get_forward_price_history(ticker, entry_date, end_date)
        fetch_time = time.time() - fetch_start
        logger.info(f"✅ Fetched {len(bars) if bars else 0} price bars in {fetch_time:.2f}s")
        
        if not bars or len(bars) < 1:
            # No data available - trade would remain open
            logger.warning(f"⚠️  No price data available for {ticker} from {entry_date} to {end_date}")
            total_cost = entry_price * quantity
            current_date_obj = datetime.now()
            entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
            hold_days = (current_date_obj - entry_date_obj).days
            
            logger.info(f"❌ Trade simulation incomplete - no data. Hold days: {hold_days}")
            total_time = time.time() - start_time
            logger.info(f"⏱️  Total simulation time: {total_time:.2f}s")
            
            return {
                "entry_date": entry_date,
                "entry_price": entry_price,
                "exit_date": None,
                "exit_price": None,
                "exit_reason": "no_data",
                "quantity": quantity,
                "total_cost": round(total_cost, 2),
                "total_proceeds": None,
                "profit_loss": None,
                "profit_loss_pct": None,
                "hold_days": hold_days,
                "price_history": [],
                "events": []
            }
        
        # Convert to DataFrame
        logger.info(f"📊 Processing {len(bars)} price bars...")
        df = pd.DataFrame(bars)
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        df['Date'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        logger.info(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        logger.info(f"   Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
        
        # Track trade
        total_cost = entry_price * quantity
        exit_reason = None
        exit_price = None
        exit_date_result = None
        events = []
        
        logger.info(f"🔍 Checking {len(df)} days for exit conditions...")
        # Check each day for exit conditions
        for date_idx, (date, row) in enumerate(df.iterrows()):
            if (date_idx + 1) % 10 == 0 or date_idx == 0:
                logger.debug(f"   Day {date_idx + 1}/{len(df)}: {date.strftime('%Y-%m-%d')} - "
                           f"High: ${row['High']:.2f}, Low: ${row['Low']:.2f}, Close: ${row['Close']:.2f}")
            
            date_str = date.strftime("%Y-%m-%d")
            high = row['High']
            low = row['Low']
            close = row['Close']
            
            # Check stop loss (triggered if low touches or goes below stop loss)
            if stop_loss and low <= stop_loss:
                exit_reason = "stop_loss"
                exit_price = stop_loss  # Use stop loss price
                exit_date_result = date_str
                logger.info(f"🛑 STOP LOSS HIT on {date_str} at ${stop_loss:.2f} (low was ${low:.2f})")
                events.append({
                    "date": date_str,
                    "event": "stop_loss_hit",
                    "price": stop_loss,
                    "low": low,
                    "high": high
                })
                break
            
            # Check take profit (triggered if high touches or goes above take profit)
            if take_profit and high >= take_profit:
                exit_reason = "take_profit"
                exit_price = take_profit  # Use take profit price
                exit_date_result = date_str
                logger.info(f"🎯 TAKE PROFIT HIT on {date_str} at ${take_profit:.2f} (high was ${high:.2f})")
                events.append({
                    "date": date_str,
                    "event": "take_profit_hit",
                    "price": take_profit,
                    "low": low,
                    "high": high
                })
                break
            
            # Check max hold days
            if max_hold_days:
                entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
                current_date_obj = date.to_pydatetime()
                days_held = (current_date_obj - entry_date_obj).days
                
                if days_held >= max_hold_days:
                    exit_reason = "max_hold_days"
                    exit_price = close  # Use closing price on max hold day
                    exit_date_result = date_str
                    logger.info(f"⏰ MAX HOLD DAYS reached on {date_str} ({days_held} days, price: ${close:.2f})")
                    events.append({
                        "date": date_str,
                        "event": "max_hold_reached",
                        "price": close,
                        "days_held": days_held
                    })
                    break
            
            # Check forced exit date
            if exit_date:
                if date_str >= exit_date:
                    exit_reason = "forced_exit"
                    exit_price = close  # Use closing price on exit date
                    exit_date_result = date_str
                    logger.info(f"📅 FORCED EXIT on {date_str} (exit date reached, price: ${close:.2f})")
                    events.append({
                        "date": date_str,
                        "event": "forced_exit",
                        "price": close
                    })
                    break
        
        # If no exit condition was met, use final available price
        if exit_reason is None:
            exit_reason = "no_exit_triggered"
            exit_price = df['Close'].iloc[-1]
            exit_date_result = df.index[-1].strftime("%Y-%m-%d")
            logger.info(f"📊 No exit condition triggered. Using final price on {exit_date_result}: ${exit_price:.2f}")
            events.append({
                "date": exit_date_result,
                "event": "simulation_ended",
                "price": exit_price
            })
        
        # Calculate results
        total_proceeds = exit_price * quantity
        profit_loss = total_proceeds - total_cost
        profit_loss_pct = (profit_loss / total_cost) * 100 if total_cost > 0 else 0
        
        # Calculate hold days
        entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
        exit_date_obj = datetime.strptime(exit_date_result, "%Y-%m-%d")
        hold_days = (exit_date_obj - entry_date_obj).days
        
        logger.info(f"💰 Trade Results:")
        logger.info(f"   Entry: ${entry_price:.2f} on {entry_date}")
        logger.info(f"   Exit: ${exit_price:.2f} on {exit_date_result} ({exit_reason})")
        logger.info(f"   Hold Duration: {hold_days} days")
        logger.info(f"   Total Cost: ${total_cost:.2f}")
        logger.info(f"   Total Proceeds: ${total_proceeds:.2f}")
        logger.info(f"   Profit/Loss: ${profit_loss:.2f} ({profit_loss_pct:+.2f}%)")
        
        # Prepare price history (simplified - just close prices)
        price_history = []
        for date, row in df.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            if date_str <= exit_date_result:
                price_history.append({
                    "date": date_str,
                    "close": float(row['Close']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "volume": int(row['Volume'])
                })
            else:
                break  # Stop once we pass the exit date
        
        total_time = time.time() - start_time
        logger.info(f"✅ Trade simulation completed in {total_time:.2f}s")
        
        return {
            "entry_date": entry_date,
            "entry_price": round(entry_price, 2),
            "exit_date": exit_date_result,
            "exit_price": round(exit_price, 2),
            "exit_reason": exit_reason,
            "quantity": quantity,
            "total_cost": round(total_cost, 2),
            "total_proceeds": round(total_proceeds, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2),
            "hold_days": hold_days,
            "price_history": price_history,
            "events": events
        }
        
    except Exception as e:
        total_time = time.time() - start_time if 'start_time' in locals() else 0
        logger.error(f"❌ Error simulating trade for {ticker} after {total_time:.2f}s: {e}")
        logger.exception("Full error traceback:")
        raise Exception(f"Trade simulation failed: {str(e)}")

