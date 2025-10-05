#!/bin/bash

echo "🚀 Fetching Ticker Universe from Polygon.io"
echo "============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3 first."
    exit 1
fi

# Run the ticker fetch script
echo "📊 Running ticker universe fetcher..."
python3 scripts/fetch_ticker_universe.py

# Check if the file was created
if [ -f "data/us_stock_universe.csv" ]; then
    echo ""
    echo "✅ SUCCESS! Ticker universe created."
    echo "📁 File: data/us_stock_universe.csv"
    
    # Show file size and line count
    file_size=$(du -h data/us_stock_universe.csv | cut -f1)
    line_count=$(wc -l < data/us_stock_universe.csv)
    echo "📊 File size: $file_size"
    echo "📊 Total lines: $line_count (including header)"
    
    echo ""
    echo "🎯 You can now use the enhanced stock screener with the full universe!"
    echo "   Example: curl 'http://localhost:8000/midas/asset/stock_screener?sector=all&limit=10'"
else
    echo ""
    echo "❌ FAILED! Ticker universe file was not created."
    echo "💡 Check the error messages above for details."
    exit 1
fi
