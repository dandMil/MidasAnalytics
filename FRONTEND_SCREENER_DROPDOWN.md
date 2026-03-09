# Frontend Screener Dropdown Implementation Guide

## Overview

The screener dropdown should only show:
1. **Universe** - Full ticker universe (all stocks)
2. **All** - All predefined sectors combined
3. **Technology/AI** - SIC-based tech sector
4. **Energy** - SIC-based energy sector
5. **Healthcare/Biotech** - SIC-based healthcare sector

## Backend API

### Get Available Sectors

**Endpoint:** `GET /midas/asset/available_sectors`

**Response:**
```json
{
  "universe": {
    "name": "Universe",
    "ticker_count": 11802,
    "tickers": ["A", "AA", "AAA", ...],
    "type": "universe",
    "value": "universe"
  },
  "all": {
    "name": "All Sectors",
    "ticker_count": 100,
    "tickers": ["AAPL", "MSFT", ...],
    "type": "all",
    "value": "all"
  },
  "tech_sic": {
    "name": "Technology/AI",
    "ticker_count": 2345,
    "tickers": ["AAPL", "MSFT", "NVDA", ...],
    "type": "sic_based",
    "available": true,
    "value": "tech_sic"
  },
  "energy_sic": {
    "name": "Energy",
    "ticker_count": 567,
    "tickers": ["XOM", "CVX", "SLB", ...],
    "type": "sic_based",
    "available": true,
    "value": "energy_sic"
  },
  "healthcare_sic": {
    "name": "Healthcare/Biotech",
    "ticker_count": 1234,
    "tickers": ["PFE", "JNJ", "ISRG", ...],
    "type": "sic_based",
    "available": true,
    "value": "healthcare_sic"
  }
}
```

## Frontend Implementation

### TypeScript/React Example

```typescript
// Types
interface Sector {
  name: string;           // Human-readable name for display
  ticker_count: number;
  type: string;
  value: string;           // Backend value to send
  available?: boolean;
}

interface SectorsResponse {
  [key: string]: Sector;
}

// Component
const ScreenerView = () => {
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>("universe");
  
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
          value: key  // Ensure value is set correctly
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
    // Trigger screener API call with selected sector
    fetchScreenerResults(sectorValue);
  };
  
  const fetchScreenerResults = async (sector: string) => {
    try {
      const params = new URLSearchParams({
        sector: sector,
        limit: '50',
        // ... other filter params
      });
      
      const response = await fetch(`/midas/asset/stock_screener?${params}`);
      const results = await response.json();
      // Handle results...
    } catch (error) {
      console.error('Error fetching screener results:', error);
    }
  };
  
  return (
    <div>
      <label>Sector:</label>
      <select 
        value={selectedSector} 
        onChange={(e) => handleSectorChange(e.target.value)}
      >
        {sectors.map((sector) => (
          <option key={sector.value} value={sector.value}>
            {sector.name} ({sector.ticker_count} stocks)
          </option>
        ))}
      </select>
    </div>
  );
};
```

### Dropdown Options

The dropdown should display:

1. **Universe** (value: `universe`)
   - Uses full ticker universe
   - Typically ~11,802 stocks

2. **All Sectors** (value: `all`)
   - Uses all predefined sectors combined
   - Typically ~100 stocks

3. **Technology/AI** (value: `tech_sic`)
   - SIC-based technology sector
   - Loads from `data/sic_tickers/tech_tickers_by_sic.csv`

4. **Energy** (value: `energy_sic`)
   - SIC-based energy sector
   - Loads from `data/sic_tickers/energy_tickers_by_sic.csv`

5. **Healthcare/Biotech** (value: `healthcare_sic`)
   - SIC-based healthcare sector
   - Loads from `data/sic_tickers/healthcare_tickers_by_sic.csv`

### Display Format

**Option 1: Simple**
```
Universe
All Sectors
Technology/AI
Energy
Healthcare/Biotech
```

**Option 2: With Counts**
```
Universe (11,802 stocks)
All Sectors (100 stocks)
Technology/AI (2,345 stocks)
Energy (567 stocks)
Healthcare/Biotech (1,234 stocks)
```

## API Call Examples

### Universe
```typescript
fetch('/midas/asset/stock_screener?sector=universe&limit=50')
```

### All Sectors
```typescript
fetch('/midas/asset/stock_screener?sector=all&limit=50')
```

### Technology/AI (SIC-based)
```typescript
fetch('/midas/asset/stock_screener?sector=tech_sic&limit=50')
```

### Energy (SIC-based)
```typescript
fetch('/midas/asset/stock_screener?sector=energy_sic&limit=50')
```

### Healthcare/Biotech (SIC-based)
```typescript
fetch('/midas/asset/stock_screener?sector=healthcare_sic&limit=50')
```

## Backend Value Mapping

| Frontend Display | Backend Value | Description |
|-----------------|---------------|-------------|
| Universe | `universe` | Full ticker universe |
| All Sectors | `all` | All predefined sectors |
| Technology/AI | `tech_sic` | SIC-based tech sector |
| Energy | `energy_sic` | SIC-based energy sector |
| Healthcare/Biotech | `healthcare_sic` | SIC-based healthcare sector |

## Implementation Checklist

- [ ] Fetch sectors from `/midas/asset/available_sectors`
- [ ] Filter to only show: universe, all, tech_sic, energy_sic, healthcare_sic
- [ ] Display human-readable names from `sector.name`
- [ ] Use `sector.value` when calling backend API
- [ ] Sort dropdown: Universe, All, then SIC sectors alphabetically
- [ ] Show ticker counts (optional but recommended)
- [ ] Handle sector selection change
- [ ] Call `/midas/asset/stock_screener` with correct sector value

## Notes

- **Universe** uses the full ticker universe (same as `sector=all` in old implementation but now explicit)
- **All** uses predefined sectors (legacy behavior)
- **SIC sectors** load from CSV files and use same history checking as universe
- If SIC CSV files don't exist, backend falls back to predefined sectors automatically
- All sectors use the same history checking and caching logic
