# services/daily_summary/daily_summary_service.py

import math
from services.intelligence.strategy_evaluator import StrategyEvaluator
from utils.market_data import fetch_polygon_ohlcv
from services.reddit.reddit_scraper import RedditScraper
from utils.polygon_client import get_top_movers
from typing import List

def clean_value(v):
    return None if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else v

def generate_daily_summary(top_n=5):
    evaluator = StrategyEvaluator()

    # Get top movers
    top_gainers = get_top_movers("gainers")[:top_n]
    top_losers = get_top_movers("losers")[:top_n]

    # Get Reddit mentions
    reddit_scraper = RedditScraper(days_back=1)
    reddit_tickers = reddit_scraper.scrape()[:top_n]

    # Combine and deduplicate tickers
    tickers = list(set([t["ticker"] for t in top_gainers + top_losers] + reddit_tickers))

    summary = []

    for ticker in tickers:
        try:
            result = evaluator.run_all_backtests(ticker, days=60)
            best_result = result[0]
            strategy_output = best_result["result"]

            summary.append({
                "ticker": ticker,
                "strategy": best_result["strategy"],
                "signal": strategy_output.get("signal", "hold"),
                "price": clean_value(strategy_output.get("price")),
                "stop_loss": clean_value(strategy_output.get("stop_loss")),
                "take_profit": clean_value(strategy_output.get("take_profit")),
                "expected_profit": clean_value(strategy_output.get("expected_profit")),
                "expected_loss": clean_value(strategy_output.get("expected_loss")),
                "total_return": clean_value(strategy_output.get("total_return", 0.0)),
                "old_logs": best_result["result"].get("log",[]),
                "log": strategy_output.get("log",[]),

            })

        except Exception as e:
            print(f"[DailySummary] Error processing {ticker}: {e}")
            continue

    print("RESPONSE FOR DAILY SUMMARY", summary)
    return summary
