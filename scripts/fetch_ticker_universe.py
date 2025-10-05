#!/usr/bin/env python3
"""
Script to fetch all US stock tickers from Polygon.io API and save to CSV.
This creates a comprehensive universe of stocks for the screener service.
"""

import requests
import csv
import time
import os
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
POLYGON_API_KEY = "q5L0XMSpFfIyyE0q_zJWgQaZ0U8aUqMK"
BASE_URL = "https://api.polygon.io/v3/reference/tickers"
OUTPUT_FILE = "data/us_stock_universe.csv"
RATE_LIMIT_DELAY = 1.0  # seconds between API calls

def fetch_tickers_page(url: str, page: int = 1) -> Optional[Dict]:
    """
    Fetch a single page of tickers from Polygon.io API.
    
    Args:
        url: API URL with parameters
        page: Page number for logging
        
    Returns:
        API response as dictionary or None if error
    """
    try:
        print(f"Fetching page {page}...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Page {page}: Retrieved {data.get('count', 0)} tickers")
            return data
        else:
            print(f"❌ Page {page}: HTTP {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Page {page}: Request failed - {e}")
        return None
    except Exception as e:
        print(f"❌ Page {page}: Unexpected error - {e}")
        return None

def filter_us_stocks(tickers: List[Dict]) -> List[Dict]:
    """
    Filter tickers to only include US stocks.
    
    Args:
        tickers: List of ticker objects from API
        
    Returns:
        Filtered list of US stock tickers
    """
    us_stocks = []
    
    for ticker in tickers:
        # Check if it's a US stock
        if (ticker.get('market') == 'stocks' and 
            ticker.get('locale') == 'us' and
            ticker.get('active', False)):
            
            # Extract relevant fields
            filtered_ticker = {
                'ticker': ticker.get('ticker', ''),
                'name': ticker.get('name', ''),
                'primary_exchange': ticker.get('primary_exchange', ''),
                'type': ticker.get('type', ''),
                'currency_name': ticker.get('currency_name', ''),
                'cik': ticker.get('cik', ''),
                'last_updated_utc': ticker.get('last_updated_utc', '')
            }
            us_stocks.append(filtered_ticker)
    
    return us_stocks

def save_to_csv(tickers: List[Dict], filename: str) -> bool:
    """
    Save tickers to CSV file.
    
    Args:
        tickers: List of ticker dictionaries
        filename: Output CSV filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if tickers:
                fieldnames = tickers[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tickers)
        
        print(f"✅ Saved {len(tickers)} tickers to {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")
        return False

def fetch_all_tickers() -> List[Dict]:
    """
    Fetch all US stock tickers by paginating through Polygon.io API.
    
    Returns:
        List of all US stock tickers
    """
    all_tickers = []
    page = 1
    next_url = None
    
    # Initial URL
    initial_url = f"{BASE_URL}?market=stocks&active=true&order=asc&limit=1000&sort=ticker&apiKey={POLYGON_API_KEY}"
    current_url = initial_url
    
    print("🚀 Starting ticker universe fetch...")
    print(f"📊 Target: All US stocks from Polygon.io")
    print(f"⏱️  Rate limit: {RATE_LIMIT_DELAY}s between calls")
    print("-" * 50)
    
    while current_url:
        # Fetch current page
        data = fetch_tickers_page(current_url, page)
        
        if not data:
            print(f"❌ Failed to fetch page {page}, stopping...")
            break
        
        # Extract tickers from current page
        page_tickers = data.get('results', [])
        if not page_tickers:
            print(f"📄 Page {page}: No tickers found, stopping...")
            break
        
        # Filter for US stocks
        us_stocks = filter_us_stocks(page_tickers)
        all_tickers.extend(us_stocks)
        
        print(f"📈 Page {page}: Added {len(us_stocks)} US stocks (Total: {len(all_tickers)})")
        
        # Check for next page
        next_url = data.get('next_url')
        if next_url:
            # Append API key to next_url since it doesn't include it
            separator = '&' if '?' in next_url else '?'
            current_url = f"{next_url}{separator}apiKey={POLYGON_API_KEY}"
            page += 1
            
            # Rate limiting
            print(f"⏳ Waiting {RATE_LIMIT_DELAY}s before next request...")
            time.sleep(RATE_LIMIT_DELAY)
        else:
            print("📄 No more pages available")
            break
    
    print("-" * 50)
    print(f"🎉 Fetch complete! Total US stocks: {len(all_tickers)}")
    return all_tickers

def main():
    """Main execution function."""
    print("=" * 60)
    print("📊 POLYGON.IO TICKER UNIVERSE FETCHER")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fetch all tickers
    all_tickers = fetch_all_tickers()
    
    if not all_tickers:
        print("❌ No tickers fetched. Exiting.")
        return
    
    # Save to CSV
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    success = save_to_csv(all_tickers, OUTPUT_FILE)
    
    if success:
        print(f"\n✅ SUCCESS!")
        print(f"📁 File: {OUTPUT_FILE}")
        print(f"📊 Total tickers: {len(all_tickers)}")
        print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show sample of tickers
        print(f"\n📋 Sample tickers:")
        for i, ticker in enumerate(all_tickers[:5]):
            print(f"  {i+1}. {ticker['ticker']} - {ticker['name']}")
        
        if len(all_tickers) > 5:
            print(f"  ... and {len(all_tickers) - 5} more")
    else:
        print("❌ Failed to save tickers to CSV")

if __name__ == "__main__":
    main()
