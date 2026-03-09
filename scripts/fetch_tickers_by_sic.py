#!/usr/bin/env python3
"""
Script to fetch all tickers belonging to specific SIC codes.
Uses Polygon.io API to get ticker details and filters by SIC code.
"""

import requests
import csv
import time
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Set

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    pass  # python-dotenv not installed, will use environment variables only

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️  tqdm not installed. Install with: pip install tqdm")
    print("   Progress bar will be disabled. Using simple progress updates instead.")

# Configuration - Load from .env file or environment variable
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io/v3/reference/tickers"
TICKER_DETAILS_URL = "https://api.polygon.io/v3/reference/tickers/{ticker}"
RATE_LIMIT_DELAY = 0.2  # seconds between API calls (5 calls per second for Pro tier)
OUTPUT_DIR = "data/sic_tickers"

# SIC Code Definitions
TECH_SIC_CODES = [
    7370, 7371, 7372, 7373, 7374, 7375, 7376, 7377, 7378, 7379,  # Software
    3570, 3571, 3572, 3575, 3577,  # Hardware
    3660, 3661, 3663, 3669,  # Communications
    3670, 3671, 3672, 3674, 3675, 3676, 3677, 3678, 3679,  # Semiconductors
    3810, 3812  # AI/Autonomous
]

ENERGY_SIC_CODES = [
    1310, 1311,  # Oil & Gas Exploration
    1380, 1381, 1382, 1389,  # Oilfield Services
    2910, 2911,  # Refining
    4610, 4612, 4613,  # Oil Pipelines
    4920, 4922, 4923, 4924, 4925,  # Gas Pipelines
    4910, 4911  # Electric Utilities
]

HEALTHCARE_SIC_CODES = [
    2830, 2831, 2833, 2834, 2835, 2836,  # Pharmaceuticals
    3840, 3841, 3842, 3843, 3844, 3845,  # Medical Devices
    8070, 8071,  # Medical Labs
    8730, 8731  # Research
]

# Convert to sets for faster lookup
TECH_SIC_SET = set(TECH_SIC_CODES)
ENERGY_SIC_SET = set(ENERGY_SIC_CODES)
HEALTHCARE_SIC_SET = set(HEALTHCARE_SIC_CODES)

def get_ticker_details(ticker: str) -> Optional[Dict]:
    """
    Get detailed information about a ticker from Polygon.io API.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Ticker details dictionary or None if error
    """
    try:
        url = TICKER_DETAILS_URL.format(ticker=ticker)
        params = {"apiKey": POLYGON_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json().get('results', {})
        elif response.status_code == 429:
            print(f"⚠️  Rate limit hit for {ticker}, waiting...")
            time.sleep(60)  # Wait 1 minute for rate limit
            return None
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error fetching details for {ticker}: {e}")
        return None

def get_sic_code_from_ticker_details(ticker_details: Dict) -> Optional[int]:
    """
    Extract SIC code from ticker details.
    Polygon.io may provide SIC code in different fields.
    
    Args:
        ticker_details: Ticker details dictionary from API
        
    Returns:
        SIC code as integer or None if not found
    """
    # Try different possible field names
    sic_code = (
        ticker_details.get('sic_code') or
        ticker_details.get('sicCode') or
        ticker_details.get('sic') or
        ticker_details.get('industry', {}).get('sic_code') or
        ticker_details.get('industry', {}).get('sicCode')
    )
    
    if sic_code:
        try:
            return int(sic_code)
        except (ValueError, TypeError):
            return None
    
    return None

def fetch_all_tickers() -> List[Dict]:
    """
    Fetch all US stock tickers from Polygon.io.
    
    Returns:
        List of ticker dictionaries
    """
    all_tickers = []
    page = 1
    next_url = None
    
    initial_url = f"{BASE_URL}?market=stocks&active=true&order=asc&limit=1000&sort=ticker&apiKey={POLYGON_API_KEY}"
    current_url = initial_url
    
    print("🚀 Fetching all US stock tickers...")
    
    # Create progress bar for fetching (we don't know total pages, so use manual updates)
    if HAS_TQDM:
        pbar_fetch = tqdm(desc="Fetching tickers", unit="page", ncols=100, bar_format='{l_bar}{bar}| {n_fmt} pages [{elapsed}] | Total: {postfix}')
        pbar_fetch.set_postfix_str("0 tickers")
    else:
        pbar_fetch = None
    
    while current_url:
        try:
            response = requests.get(current_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tickers = data.get('results', [])
                
                # Filter for US stocks
                us_stocks = [
                    t for t in tickers
                    if (t.get('market') == 'stocks' and 
                        t.get('locale') == 'us' and
                        t.get('active', False))
                ]
                
                all_tickers.extend(us_stocks)
                
                if HAS_TQDM and pbar_fetch is not None:
                    pbar_fetch.update(1)
                    pbar_fetch.set_postfix_str(f"{len(all_tickers)} tickers")
                else:
                    print(f"📄 Page {page}: Added {len(us_stocks)} tickers (Total: {len(all_tickers)})")
                
                next_url = data.get('next_url')
                if next_url:
                    separator = '&' if '?' in next_url else '?'
                    current_url = f"{next_url}{separator}apiKey={POLYGON_API_KEY}"
                    page += 1
                    time.sleep(RATE_LIMIT_DELAY)
                else:
                    break
            elif response.status_code == 429:
                if HAS_TQDM and pbar_fetch is not None:
                    pbar_fetch.write("⚠️  Rate limit hit, waiting 60 seconds...")
                else:
                    print("⚠️  Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
            else:
                if HAS_TQDM and pbar_fetch is not None:
                    pbar_fetch.write(f"❌ Error: HTTP {response.status_code}")
                else:
                    print(f"❌ Error: HTTP {response.status_code}")
                break
                
        except Exception as e:
            if HAS_TQDM and pbar_fetch is not None:
                pbar_fetch.write(f"❌ Error fetching page {page}: {e}")
            else:
                print(f"❌ Error fetching page {page}: {e}")
            break
    
    if HAS_TQDM and pbar_fetch is not None:
        pbar_fetch.close()
    
    print(f"✅ Fetched {len(all_tickers)} total tickers")
    return all_tickers

def classify_ticker_by_sic(ticker: str, sic_code: Optional[int]) -> Optional[str]:
    """
    Classify ticker into sector based on SIC code.
    
    Args:
        ticker: Ticker symbol
        sic_code: SIC code
        
    Returns:
        Sector name ('tech', 'energy', 'healthcare') or None
    """
    if sic_code is None:
        return None
    
    # Check if SIC code matches any sector
    if sic_code in TECH_SIC_SET:
        return 'tech'
    elif sic_code in ENERGY_SIC_SET:
        return 'energy'
    elif sic_code in HEALTHCARE_SIC_SET:
        return 'healthcare'
    
    return None

def fetch_tickers_by_sic_codes() -> Dict[str, List[Dict]]:
    """
    Fetch all tickers and classify them by SIC codes.
    
    Returns:
        Dictionary with sectors as keys and lists of tickers as values
    """
    print("=" * 60)
    print("📊 FETCHING TICKERS BY SIC CODES")
    print("=" * 60)
    
    # Fetch all tickers
    all_tickers = fetch_all_tickers()
    
    if not all_tickers:
        print("❌ No tickers fetched")
        return {}
    
    # Classify tickers by SIC code
    classified = {
        'tech': [],
        'energy': [],
        'healthcare': []
    }
    
    total = len(all_tickers)
    processed = 0
    no_sic_count = 0
    found_sic = 0
    
    print(f"\n🔍 Classifying {total} tickers by SIC code...")
    print("⏱️  This may take a while due to API rate limits...")
    print("-" * 60)
    
    # Create progress bar for classification
    if HAS_TQDM:
        pbar = tqdm(
            all_tickers,
            desc="Classifying tickers",
            unit="ticker",
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] | {postfix}'
        )
        pbar.set_postfix_str("SIC: 0 | Tech:0 Energy:0 Health:0")
    else:
        pbar = all_tickers
    
    for i, ticker_info in enumerate(pbar):
        ticker = ticker_info.get('ticker', '')
        
        if not ticker:
            continue
        
        processed += 1
        
        # Get ticker details to find SIC code
        ticker_details = get_ticker_details(ticker)
        
        if not ticker_details:
            no_sic_count += 1
            if HAS_TQDM:
                pbar.set_postfix_str(
                    f"SIC: {found_sic} | "
                    f"Tech:{len(classified['tech'])} "
                    f"Energy:{len(classified['energy'])} "
                    f"Health:{len(classified['healthcare'])} "
                    f"NoSIC:{no_sic_count}"
                )
            elif processed % 100 == 0:
                print(f"📊 Progress: {processed}/{total} ({100*processed/total:.1f}%) | No SIC: {no_sic_count}")
            time.sleep(RATE_LIMIT_DELAY)
            continue
        
        # Extract SIC code
        sic_code = get_sic_code_from_ticker_details(ticker_details)
        
        if sic_code:
            found_sic += 1
        
        # Classify by sector
        sector = classify_ticker_by_sic(ticker, sic_code)
        
        if sector:
            ticker_data = {
                'ticker': ticker,
                'name': ticker_info.get('name', ''),
                'sic_code': sic_code,
                'primary_exchange': ticker_info.get('primary_exchange', ''),
                'type': ticker_info.get('type', ''),
                'currency_name': ticker_info.get('currency_name', ''),
                'cik': ticker_info.get('cik', ''),
            }
            classified[sector].append(ticker_data)
            
            if HAS_TQDM:
                pbar.set_postfix_str(
                    f"SIC: {found_sic} | "
                    f"Tech:{len(classified['tech'])} "
                    f"Energy:{len(classified['energy'])} "
                    f"Health:{len(classified['healthcare'])}"
                )
            else:
                print(f"✅ {ticker}: {sector.upper()} (SIC: {sic_code})")
        
        # Update progress bar
        if HAS_TQDM:
            found_sic = processed - no_sic_count
            pbar.set_postfix_str(
                f"SIC: {found_sic} | "
                f"Tech:{len(classified['tech'])} "
                f"Energy:{len(classified['energy'])} "
                f"Health:{len(classified['healthcare'])}"
            )
        elif processed % 50 == 0:
            # Fallback progress update if tqdm not available
            print(f"📊 Progress: {processed}/{total} ({100*processed/total:.1f}%) | "
                  f"Tech: {len(classified['tech'])}, "
                  f"Energy: {len(classified['energy'])}, "
                  f"Healthcare: {len(classified['healthcare'])}")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    # Close progress bar
    if HAS_TQDM:
        pbar.close()
    
    print("-" * 60)
    print(f"✅ Classification complete!")
    print(f"📊 Tech: {len(classified['tech'])} tickers")
    print(f"📊 Energy: {len(classified['energy'])} tickers")
    print(f"📊 Healthcare: {len(classified['healthcare'])} tickers")
    print(f"⚠️  No SIC code found: {no_sic_count} tickers")
    
    return classified

def save_tickers_to_csv(classified: Dict[str, List[Dict]]):
    """
    Save classified tickers to CSV files.
    
    Args:
        classified: Dictionary with sectors and ticker lists
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for sector, tickers in classified.items():
        if not tickers:
            print(f"⚠️  No tickers found for {sector}")
            continue
        
        filename = f"{OUTPUT_DIR}/{sector}_tickers_by_sic.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = tickers[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tickers)
            
            print(f"✅ Saved {len(tickers)} {sector} tickers to {filename}")
        except Exception as e:
            print(f"❌ Error saving {sector} tickers: {e}")

def save_tickers_to_json(classified: Dict[str, List[Dict]]):
    """
    Save classified tickers to JSON file.
    
    Args:
        classified: Dictionary with sectors and ticker lists
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"{OUTPUT_DIR}/all_tickers_by_sic.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(classified, f, indent=2, ensure_ascii=False)
        
        total = sum(len(tickers) for tickers in classified.values())
        print(f"✅ Saved {total} total tickers to {filename}")
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")

def main():
    """Main execution function."""
    if not POLYGON_API_KEY:
        print("❌ POLYGON_API_KEY not found!")
        print("   Please set it in one of these ways:")
        print("   1. Add to .env file: POLYGON_API_KEY=your_key_here")
        print("   2. Export as environment variable: export POLYGON_API_KEY=your_key_here")
        print("   3. Install python-dotenv: pip install python-dotenv")
        return
    
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fetch and classify tickers
    classified = fetch_tickers_by_sic_codes()
    
    if not classified:
        print("❌ No tickers classified")
        return
    
    # Save results
    print(f"\n💾 Saving results...")
    save_tickers_to_csv(classified)
    save_tickers_to_json(classified)
    
    print(f"\n✅ COMPLETE!")
    print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Technology/AI: {len(classified['tech'])} tickers")
    print(f"  Energy: {len(classified['energy'])} tickers")
    print(f"  Healthcare/Biotech: {len(classified['healthcare'])} tickers")
    print(f"  Total: {sum(len(tickers) for tickers in classified.values())} tickers")

if __name__ == "__main__":
    main()
