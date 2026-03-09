#!/usr/bin/env python3
"""
Simplified script to get tickers by SIC code.
Uses existing ticker universe and attempts to get SIC codes from multiple sources.
"""

import csv
import os
import requests
import time
from typing import List, Dict, Set, Optional

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

# SIC Code Definitions
TECH_SIC_CODES = set([
    7370, 7371, 7372, 7373, 7374, 7375, 7376, 7377, 7378, 7379,  # Software
    3570, 3571, 3572, 3575, 3577,  # Hardware
    3660, 3661, 3663, 3669,  # Communications
    3670, 3671, 3672, 3674, 3675, 3676, 3677, 3678, 3679,  # Semiconductors
    3810, 3812  # AI/Autonomous
])

ENERGY_SIC_CODES = set([
    1310, 1311,  # Oil & Gas Exploration
    1380, 1381, 1382, 1389,  # Oilfield Services
    2910, 2911,  # Refining
    4610, 4612, 4613,  # Oil Pipelines
    4920, 4922, 4923, 4924, 4925,  # Gas Pipelines
    4910, 4911  # Electric Utilities
])

HEALTHCARE_SIC_CODES = set([
    2830, 2831, 2833, 2834, 2835, 2836,  # Pharmaceuticals
    3840, 3841, 3842, 3843, 3844, 3845,  # Medical Devices
    8070, 8071,  # Medical Labs
    8730, 8731  # Research
])

def get_sic_from_sec_edgar(cik: str) -> Optional[int]:
    """
    Get SIC code from SEC EDGAR using CIK.
    This is a simplified approach - in production you'd use the full SEC API.
    """
    if not cik or cik == '':
        return None
    
    # SEC EDGAR company facts endpoint
    # Note: This is a simplified example - actual implementation would need proper SEC API calls
    try:
        # SEC company facts API (free, no auth required)
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        headers = {
            'User-Agent': 'MidasAnalytics/1.0 (contact@example.com)',  # SEC requires User-Agent
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # SIC code is typically in the company data
            sic = data.get('sic', '')
            if sic:
                try:
                    return int(sic)
                except (ValueError, TypeError):
                    return None
        
        time.sleep(0.1)  # SEC rate limit: 10 requests per second
    except Exception as e:
        pass  # Silently fail and try other methods
    
    return None

def get_sic_from_polygon(ticker: str, api_key: str) -> Optional[int]:
    """
    Get SIC code from Polygon.io ticker details.
    """
    try:
        url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
        params = {"apiKey": api_key}
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('results', {})
            sic = data.get('sic_code') or data.get('sicCode')
            if sic:
                try:
                    return int(sic)
                except (ValueError, TypeError):
                    return None
        
        time.sleep(0.2)  # Polygon rate limit
    except Exception:
        pass
    
    return None

def load_ticker_universe(csv_path: str = "data/us_stock_universe.csv") -> List[Dict]:
    """Load tickers from existing universe CSV."""
    if not os.path.exists(csv_path):
        print(f"❌ Ticker universe file not found: {csv_path}")
        return []
    
    tickers = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickers.append(row)
    
    return tickers

def classify_by_sic(sic_code: Optional[int]) -> Optional[str]:
    """Classify ticker into sector based on SIC code."""
    if sic_code is None:
        return None
    
    if sic_code in TECH_SIC_CODES:
        return 'tech'
    elif sic_code in ENERGY_SIC_CODES:
        return 'energy'
    elif sic_code in HEALTHCARE_SIC_CODES:
        return 'healthcare'
    
    return None

def get_tickers_by_sic(use_polygon: bool = True, limit: Optional[int] = None) -> Dict[str, List[Dict]]:
    """
    Get tickers classified by SIC codes.
    
    Args:
        use_polygon: Whether to use Polygon.io API (requires API key)
        limit: Limit number of tickers to process (for testing)
    """
    print("=" * 60)
    print("📊 GETTING TICKERS BY SIC CODES")
    print("=" * 60)
    
    # Load existing ticker universe
    print("📂 Loading ticker universe...")
    all_tickers = load_ticker_universe()
    
    if not all_tickers:
        print("❌ No tickers loaded")
        return {}
    
    if limit:
        all_tickers = all_tickers[:limit]
        print(f"⚠️  Limited to first {limit} tickers for testing")
    
    print(f"✅ Loaded {len(all_tickers)} tickers")
    
    # Classify tickers
    classified = {
        'tech': [],
        'energy': [],
        'healthcare': []
    }
    
    polygon_api_key = os.getenv("POLYGON_API_KEY") if use_polygon else None
    
    print(f"\n🔍 Classifying tickers by SIC code...")
    print(f"   Using Polygon API: {'Yes' if polygon_api_key else 'No'}")
    print("-" * 60)
    
    processed = 0
    found_sic = 0
    
    # Create progress bar
    if HAS_TQDM:
        pbar = tqdm(
            all_tickers,
            desc="Processing tickers",
            unit="ticker",
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] | SIC: {postfix}'
        )
        pbar.set_postfix_str("0 found")
    else:
        pbar = all_tickers
    
    for ticker_info in pbar:
        ticker = ticker_info.get('ticker', '')
        cik = ticker_info.get('cik', '')
        
        if not ticker:
            continue
        
        processed += 1
        
        # Try to get SIC code
        sic_code = None
        
        # Method 1: Try Polygon.io if available
        if polygon_api_key:
            sic_code = get_sic_from_polygon(ticker, polygon_api_key)
        
        # Method 2: Try SEC EDGAR if CIK available
        if not sic_code and cik:
            sic_code = get_sic_from_sec_edgar(cik)
        
        # Classify by sector
        if sic_code:
            found_sic += 1
            sector = classify_by_sic(sic_code)
            
            if sector:
                ticker_data = {
                    'ticker': ticker,
                    'name': ticker_info.get('name', ''),
                    'sic_code': sic_code,
                    'primary_exchange': ticker_info.get('primary_exchange', ''),
                    'type': ticker_info.get('type', ''),
                    'cik': cik,
                }
                classified[sector].append(ticker_data)
                
                # Update progress bar with found ticker info
                if HAS_TQDM:
                    pbar.set_postfix_str(
                        f"{found_sic} found | "
                        f"Tech:{len(classified['tech'])} "
                        f"Energy:{len(classified['energy'])} "
                        f"Health:{len(classified['healthcare'])}"
                    )
                else:
                    print(f"✅ {ticker}: {sector.upper()} (SIC: {sic_code})")
        
        # Update progress bar
        if HAS_TQDM:
            pbar.set_postfix_str(
                f"{found_sic} found | "
                f"Tech:{len(classified['tech'])} "
                f"Energy:{len(classified['energy'])} "
                f"Health:{len(classified['healthcare'])}"
            )
        elif processed % 100 == 0:
            # Fallback progress update if tqdm not available
            print(f"📊 Progress: {processed}/{len(all_tickers)} | "
                  f"Found SIC: {found_sic} | "
                  f"Tech: {len(classified['tech'])}, "
                  f"Energy: {len(classified['energy'])}, "
                  f"Healthcare: {len(classified['healthcare'])}")
    
    # Close progress bar
    if HAS_TQDM:
        pbar.close()
    
    print("-" * 60)
    print(f"✅ Complete!")
    print(f"📊 Processed: {processed} tickers")
    print(f"📊 Found SIC codes: {found_sic}")
    print(f"📊 Tech: {len(classified['tech'])} tickers")
    print(f"📊 Energy: {len(classified['energy'])} tickers")
    print(f"📊 Healthcare: {len(classified['healthcare'])} tickers")
    
    return classified

def save_results(classified: Dict[str, List[Dict]], output_dir: str = "data/sic_tickers"):
    """Save classified tickers to CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    
    for sector, tickers in classified.items():
        if not tickers:
            continue
        
        filename = f"{output_dir}/{sector}_tickers_by_sic.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if tickers:
                fieldnames = tickers[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tickers)
        
        print(f"✅ Saved {len(tickers)} {sector} tickers to {filename}")

def main():
    """Main execution."""
    print("🚀 Starting SIC code classification...")
    print()
    
    # Get tickers by SIC
    # Note: For full run, remove limit parameter
    # For testing, use limit=100 to test with first 100 tickers
    classified = get_tickers_by_sic(use_polygon=True, limit=None)
    
    if not any(classified.values()):
        print("\n⚠️  No tickers classified. This could mean:")
        print("   1. Polygon API key not set or invalid")
        print("   2. Rate limits hit")
        print("   3. SIC codes not available in data sources")
        return
    
    # Save results
    print(f"\n💾 Saving results...")
    save_results(classified)
    
    print(f"\n✅ DONE!")
    total = sum(len(tickers) for tickers in classified.values())
    print(f"📊 Total tickers classified: {total}")

if __name__ == "__main__":
    main()
