# Backtesting View - Sector Dropdown Implementation Guide

## Overview

This guide shows how to add a sector dropdown to the backtesting view, following the same pattern as the screener dropdown.

## Workflow

The backtesting view should follow this workflow:
1. **Step 1: Select Sector** (Required)
2. **Step 2: Select Time Range** (Required)
3. **Step 3: Configure Options** (Optional)

---

## Backend API

### Get Available Sectors

**Endpoint:** `GET /midas/asset/available_sectors`

**Response:**
```json
{
  "universe": {
    "name": "Universe",
    "ticker_count": 11802,
    "value": "universe",
    "type": "universe"
  },
  "all": {
    "name": "All Sectors",
    "ticker_count": 100,
    "value": "all",
    "type": "all"
  },
  "tech_sic": {
    "name": "Technology/AI",
    "ticker_count": 563,
    "value": "tech_sic",
    "type": "sic_based",
    "available": true
  },
  "energy_sic": {
    "name": "Energy",
    "ticker_count": 567,
    "value": "energy_sic",
    "type": "sic_based",
    "available": true
  },
  "healthcare_sic": {
    "name": "Healthcare/Biotech",
    "ticker_count": 1234,
    "value": "healthcare_sic",
    "type": "sic_based",
    "available": true
  }
}
```

### Single Date Backtest

**Endpoint:** `GET /midas/backtest/historical_rankings`

**Parameters:**
- `sector`: **Required** - Sector to analyze
- `reference_date`: **Required** - Date in YYYY-MM-DD format
- `top_n`: Number of top stocks (default: 50)
- Other filters: `min_price`, `max_price`, `min_adr`, `max_adr`, etc.

**Example:**
```bash
GET /midas/backtest/historical_rankings?sector=tech&reference_date=2024-01-15&top_n=50
```

### Time Range Backtest

**Endpoint:** `GET /midas/backtest/historical_rankings_range`

**Parameters:**
- `sector`: **Required** - Sector to analyze (must be first)
- `start_date`: **Required** - Start date in YYYY-MM-DD format
- `end_date`: **Required** - End date in YYYY-MM-DD format
- `date_interval`: Interval between dates - `"daily"`, `"weekly"`, or `"monthly"` (default: `"weekly"`)
- `top_n`: Number of top stocks per date (default: 50)
- Other filters: Same as single date backtest

**Example:**
```bash
GET /midas/backtest/historical_rankings_range?sector=tech&start_date=2024-01-01&end_date=2024-03-31&date_interval=weekly&top_n=50
```

---

## Frontend Implementation

### React/TypeScript Example

```typescript
import React, { useState, useEffect } from 'react';

interface Sector {
  name: string;
  ticker_count: number;
  value: string;
  type: string;
  available?: boolean;
}

interface SectorsResponse {
  [key: string]: Sector;
}

const BacktestingView: React.FC = () => {
  // Step 1: Sector Selection
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>('universe');
  
  // Step 2: Time Range Selection
  const [referenceDate, setReferenceDate] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [dateInterval, setDateInterval] = useState<string>('weekly');
  const [backtestMode, setBacktestMode] = useState<'single' | 'range'>('single');
  
  // Results
  const [rankings, setRankings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch available sectors on mount
  useEffect(() => {
    fetchAvailableSectors();
  }, []);

  const fetchAvailableSectors = async () => {
    try {
      const response = await fetch('/midas/asset/available_sectors');
      const data: SectorsResponse = await response.json();
      
      // Filter to only show: universe, all, and SIC-based sectors
      const allowedSectors = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
      
      const filteredSectors = Object.entries(data)
        .filter(([key]) => allowedSectors.includes(key))
        .map(([key, sector]) => ({
          ...sector,
          value: key
        }))
        .sort((a, b) => {
          // Sort order: Universe, All, then SIC sectors alphabetically
          const order = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
          return order.indexOf(a.value) - order.indexOf(b.value);
        });
      
      setSectors(filteredSectors);
    } catch (error) {
      console.error('Error fetching sectors:', error);
    }
  };

  const handleSectorChange = (sectorValue: string) => {
    setSelectedSector(sectorValue);
    // Clear previous results when sector changes
    setRankings([]);
  };

  const handleRunBacktest = async () => {
    if (!selectedSector) {
      alert('Please select a sector first');
      return;
    }

    setLoading(true);
    try {
      if (backtestMode === 'single') {
        if (!referenceDate) {
          alert('Please select a reference date');
          setLoading(false);
          return;
        }
        await runSingleDateBacktest();
      } else {
        if (!startDate || !endDate) {
          alert('Please select start and end dates');
          setLoading(false);
          return;
        }
        await runTimeRangeBacktest();
      }
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Failed to run backtest. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const runSingleDateBacktest = async () => {
    const params = new URLSearchParams({
      sector: selectedSector,
      reference_date: referenceDate,
      top_n: '50'
    });
    
    const response = await fetch(`/midas/backtest/historical_rankings?${params}`);
    const data = await response.json();
    
    if (data.rankings) {
      setRankings(data.rankings);
    }
  };

  const runTimeRangeBacktest = async () => {
    const params = new URLSearchParams({
      sector: selectedSector,
      start_date: startDate,
      end_date: endDate,
      date_interval: dateInterval,
      top_n: '50'
    });
    
    const response = await fetch(`/midas/backtest/historical_rankings_range?${params}`);
    const data = await response.json();
    
    if (data.results) {
      // Handle time range results (multiple dates)
      // You may want to display this differently than single date results
      setRankings(data.results);
    }
  };

  return (
    <div className="backtesting-view">
      <h2>Backtesting</h2>
      
      {/* Step 1: Sector Selection */}
      <div className="form-section">
        <label htmlFor="sector-select">Step 1: Select Sector (Required)</label>
        <select
          id="sector-select"
          value={selectedSector}
          onChange={(e) => handleSectorChange(e.target.value)}
          disabled={loading}
        >
          {sectors.map((sector) => (
            <option key={sector.value} value={sector.value}>
              {sector.name} ({sector.ticker_count.toLocaleString()} stocks)
            </option>
          ))}
        </select>
      </div>

      {/* Step 2: Time Range Selection */}
      <div className="form-section">
        <label>Step 2: Select Time Range (Required)</label>
        
        <div className="backtest-mode-selector">
          <label>
            <input
              type="radio"
              value="single"
              checked={backtestMode === 'single'}
              onChange={(e) => setBacktestMode(e.target.value as 'single' | 'range')}
            />
            Single Date
          </label>
          <label>
            <input
              type="radio"
              value="range"
              checked={backtestMode === 'range'}
              onChange={(e) => setBacktestMode(e.target.value as 'single' | 'range')}
            />
            Date Range
          </label>
        </div>

        {backtestMode === 'single' ? (
          <div>
            <label htmlFor="reference-date">Reference Date:</label>
            <input
              id="reference-date"
              type="date"
              value={referenceDate}
              onChange={(e) => setReferenceDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              disabled={loading}
            />
          </div>
        ) : (
          <div>
            <label htmlFor="start-date">Start Date:</label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              disabled={loading}
            />
            
            <label htmlFor="end-date">End Date:</label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              min={startDate}
              disabled={loading}
            />
            
            <label htmlFor="date-interval">Interval:</label>
            <select
              id="date-interval"
              value={dateInterval}
              onChange={(e) => setDateInterval(e.target.value)}
              disabled={loading}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        )}
      </div>

      {/* Step 3: Run Backtest */}
      <div className="form-section">
        <button
          onClick={handleRunBacktest}
          disabled={loading || !selectedSector || (backtestMode === 'single' ? !referenceDate : !startDate || !endDate)}
        >
          {loading ? 'Running Backtest...' : 'Run Backtest'}
        </button>
      </div>

      {/* Results */}
      {rankings.length > 0 && (
        <div className="results-section">
          <h3>Historical Rankings</h3>
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Price</th>
                <th>ADR %</th>
                <th>1M %</th>
                <th>3M %</th>
                <th>RSI</th>
                <th>Signal</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((stock, idx) => (
                <tr key={idx}>
                  <td>{stock.ticker}</td>
                  <td>${stock.current_price?.toFixed(2)}</td>
                  <td>{stock.adr_percentage?.toFixed(2)}%</td>
                  <td>{stock.performance_1m?.toFixed(2)}%</td>
                  <td>{stock.performance_3m?.toFixed(2)}%</td>
                  <td>{stock.rsi?.toFixed(2)}</td>
                  <td>{stock.overall_signal}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default BacktestingView;
```

---

## Key Implementation Points

### 1. Sector Dropdown

- **Fetch sectors** from `/midas/asset/available_sectors`
- **Filter** to only show: `universe`, `all`, `tech_sic`, `energy_sic`, `healthcare_sic`
- **Display** human-readable names (e.g., "Technology/AI" instead of "tech_sic")
- **Use** `sector.value` when making API calls

### 2. Workflow Order

The UI should enforce the workflow:
1. **First**: Select sector (required)
2. **Then**: Select time range (required)
3. **Finally**: Run backtest

### 3. Single Date vs. Date Range

- **Single Date**: Use `/midas/backtest/historical_rankings` endpoint
- **Date Range**: Use `/midas/backtest/historical_rankings_range` endpoint

### 4. Validation

- Ensure sector is selected before allowing time range selection
- Ensure dates are selected before allowing backtest to run
- Validate that dates are not in the future
- Validate that end_date >= start_date for range mode

---

## Sector Options

| Display Name | Backend Value | Description |
|-------------|---------------|-------------|
| Universe | `universe` | Full ticker universe (~11,802 stocks) |
| All Sectors | `all` | All predefined sectors combined |
| Technology/AI | `tech_sic` | SIC-based tech sector (563 stocks) |
| Energy | `energy_sic` | SIC-based energy sector (567 stocks) |
| Healthcare/Biotech | `healthcare_sic` | SIC-based healthcare sector (1,234 stocks) |

---

## Example API Calls

### Single Date Backtest
```javascript
// Step 1: Sector = tech
// Step 2: Reference Date = 2024-01-15
fetch('/midas/backtest/historical_rankings?sector=tech&reference_date=2024-01-15&top_n=50')
```

### Time Range Backtest
```javascript
// Step 1: Sector = tech
// Step 2: Start = 2024-01-01, End = 2024-03-31, Interval = weekly
fetch('/midas/backtest/historical_rankings_range?sector=tech&start_date=2024-01-01&end_date=2024-03-31&date_interval=weekly&top_n=50')
```

---

## Styling Suggestions

- Make the sector dropdown prominent (first step)
- Use visual indicators (numbers or steps) to show the workflow
- Disable time range inputs until sector is selected
- Show loading state during backtest execution
- Display results in a clear table or chart format

---

## Notes

- The sector parameter is **required** for both endpoints
- Predefined sectors (`tech`, `energy`, `bio`) automatically use SIC-based data when available
- Results are cached per date, so subsequent runs are faster
- For time range backtests, results include rankings for each date in the range
