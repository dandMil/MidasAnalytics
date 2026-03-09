# Frontend Screener Dropdown Implementation

## Requirements

The dropdown should **only** show:
1. **Universe** - Full ticker universe (~11,802 stocks)
2. **All** - All predefined sectors combined
3. **Technology/AI** - SIC-based tech sector
4. **Energy** - SIC-based energy sector  
5. **Healthcare/Biotech** - SIC-based healthcare sector

## Backend API Response

### Endpoint: `GET /midas/asset/available_sectors`

**Response Structure:**
```json
{
  "universe": {
    "name": "Universe",
    "ticker_count": 11802,
    "type": "universe",
    "value": "universe"
  },
  "all": {
    "name": "All Sectors",
    "ticker_count": 100,
    "type": "all",
    "value": "all"
  },
  "tech_sic": {
    "name": "Technology/AI",
    "ticker_count": 2345,
    "type": "sic_based",
    "available": true,
    "value": "tech_sic"
  },
  "energy_sic": {
    "name": "Energy",
    "ticker_count": 567,
    "type": "sic_based",
    "available": true,
    "value": "energy_sic"
  },
  "healthcare_sic": {
    "name": "Healthcare/Biotech",
    "ticker_count": 1234,
    "type": "sic_based",
    "available": true,
    "value": "healthcare_sic"
  }
}
```

## Frontend Implementation

### React/TypeScript Example

```typescript
import React, { useState, useEffect } from 'react';

interface Sector {
  name: string;
  ticker_count: number;
  type: string;
  value: string;
  available?: boolean;
}

interface SectorsResponse {
  [key: string]: Sector;
}

const ScreenerView: React.FC = () => {
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>('universe');
  const [loading, setLoading] = useState(false);

  // Fetch available sectors on component mount
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

  const handleSectorChange = async (sectorValue: string) => {
    setSelectedSector(sectorValue);
    setLoading(true);
    
    try {
      // Call screener API with selected sector
      await fetchScreenerResults(sectorValue);
    } catch (error) {
      console.error('Error fetching screener results:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScreenerResults = async (sector: string) => {
    const params = new URLSearchParams({
      sector: sector,
      limit: '50',
      // Add other filter params as needed
    });
    
    const response = await fetch(`/midas/asset/stock_screener?${params}`);
    const results = await response.json();
    
    // Handle results (update state, display, etc.)
    console.log('Screener results:', results);
    return results;
  };

  return (
    <div className="screener-view">
      <div className="sector-selector">
        <label htmlFor="sector-select">Sector:</label>
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
      
      {loading && <div>Loading...</div>}
      
      {/* Display screener results here */}
    </div>
  );
};

export default ScreenerView;
```

### Vue.js Example

```vue
<template>
  <div class="screener-view">
    <div class="sector-selector">
      <label for="sector-select">Sector:</label>
      <select
        id="sector-select"
        v-model="selectedSector"
        @change="handleSectorChange"
        :disabled="loading"
      >
        <option
          v-for="sector in sectors"
          :key="sector.value"
          :value="sector.value"
        >
          {{ sector.name }} ({{ sector.ticker_count.toLocaleString() }} stocks)
        </option>
      </select>
    </div>
    
    <div v-if="loading">Loading...</div>
    
    <!-- Display screener results here -->
  </div>
</template>

<script>
export default {
  data() {
    return {
      sectors: [],
      selectedSector: 'universe',
      loading: false
    };
  },
  
  mounted() {
    this.fetchAvailableSectors();
  },
  
  methods: {
    async fetchAvailableSectors() {
      try {
        const response = await fetch('/midas/asset/available_sectors');
        const data = await response.json();
        
        const allowedSectors = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
        
        this.sectors = Object.entries(data)
          .filter(([key]) => allowedSectors.includes(key))
          .map(([key, sector]) => ({
            ...sector,
            value: key
          }))
          .sort((a, b) => {
            const order = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
            return order.indexOf(a.value) - order.indexOf(b.value);
          });
      } catch (error) {
        console.error('Error fetching sectors:', error);
      }
    },
    
    async handleSectorChange() {
      this.loading = true;
      
      try {
        const params = new URLSearchParams({
          sector: this.selectedSector,
          limit: '50'
        });
        
        const response = await fetch(`/midas/asset/stock_screener?${params}`);
        const results = await response.json();
        
        // Handle results
        console.log('Screener results:', results);
      } catch (error) {
        console.error('Error fetching screener results:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### Vanilla JavaScript Example

```javascript
// Fetch and populate dropdown
async function initializeScreenerDropdown() {
  try {
    const response = await fetch('/midas/asset/available_sectors');
    const data = await response.json();
    
    const allowedSectors = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
    const sectorSelect = document.getElementById('sector-select');
    
    // Clear existing options
    sectorSelect.innerHTML = '';
    
    // Filter and sort sectors
    const sectors = Object.entries(data)
      .filter(([key]) => allowedSectors.includes(key))
      .map(([key, sector]) => ({
        ...sector,
        value: key
      }))
      .sort((a, b) => {
        const order = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
        return order.indexOf(a.value) - order.indexOf(b.value);
      });
    
    // Populate dropdown
    sectors.forEach(sector => {
      const option = document.createElement('option');
      option.value = sector.value;
      option.textContent = `${sector.name} (${sector.ticker_count.toLocaleString()} stocks)`;
      sectorSelect.appendChild(option);
    });
    
    // Handle change event
    sectorSelect.addEventListener('change', async (e) => {
      const selectedSector = e.target.value;
      await fetchScreenerResults(selectedSector);
    });
    
  } catch (error) {
    console.error('Error initializing dropdown:', error);
  }
}

async function fetchScreenerResults(sector) {
  try {
    const params = new URLSearchParams({
      sector: sector,
      limit: '50'
    });
    
    const response = await fetch(`/midas/asset/stock_screener?${params}`);
    const results = await response.json();
    
    // Display results
    console.log('Screener results:', results);
    // Update UI with results...
    
  } catch (error) {
    console.error('Error fetching screener results:', error);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeScreenerDropdown);
```

## Sector Value Mapping

| Display Name | Backend Value | Description |
|--------------|---------------|-------------|
| Universe | `universe` | Full ticker universe (~11,802 stocks) |
| All Sectors | `all` | All predefined sectors combined |
| Technology/AI | `tech_sic` | SIC-based technology sector |
| Energy | `energy_sic` | SIC-based energy sector |
| Healthcare/Biotech | `healthcare_sic` | SIC-based healthcare sector |

## Key Points

1. **Filter Sectors**: Only show `universe`, `all`, `tech_sic`, `energy_sic`, `healthcare_sic`
2. **Display Names**: Use `sector.name` for human-readable labels
3. **Backend Values**: Use `sector.value` when calling the API
4. **Sort Order**: Universe → All → SIC sectors (alphabetically)
5. **API Call**: Call `/midas/asset/stock_screener?sector={value}` when selection changes

## Testing

Test each sector selection:

```bash
# Universe
curl "http://localhost:8000/midas/asset/stock_screener?sector=universe&limit=10"

# All Sectors
curl "http://localhost:8000/midas/asset/stock_screener?sector=all&limit=10"

# Technology/AI (SIC-based)
curl "http://localhost:8000/midas/asset/stock_screener?sector=tech_sic&limit=10"

# Energy (SIC-based)
curl "http://localhost:8000/midas/asset/stock_screener?sector=energy_sic&limit=10"

# Healthcare/Biotech (SIC-based)
curl "http://localhost:8000/midas/asset/stock_screener?sector=healthcare_sic&limit=10"
```

## Expected Behavior

1. **Dropdown loads** with 5 options: Universe, All, Technology/AI, Energy, Healthcare/Biotech
2. **User selects** a sector from dropdown
3. **Frontend calls** `/midas/asset/stock_screener?sector={selected_value}`
4. **Backend processes** using appropriate ticker list:
   - `universe`: Full ticker universe
   - `all`: Predefined sectors
   - `tech_sic`, `energy_sic`, `healthcare_sic`: SIC CSV files
5. **Results returned** with same format as before
6. **History checking** works identically for all sectors
