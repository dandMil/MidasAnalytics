# Screener Dropdown Debugging Guide

## ✅ Backend Status: WORKING

The backend is correctly configured and returning `tech_sic` sector:

### API Endpoint: `GET /midas/asset/available_sectors`

**Response includes:**
```json
{
  "tech_sic": {
    "name": "Technology/AI",
    "value": "tech_sic",
    "available": true,
    "ticker_count": 563,
    "type": "sic_based"
  }
}
```

### Screener Endpoint: `GET /midas/asset/stock_screener?sector=tech_sic`

**Status:** ✅ Working - Returns results when filters are appropriate

**Test Command:**
```bash
curl "http://localhost:8000/midas/asset/stock_screener?sector=tech_sic&limit=3&min_1m_performance=0&min_3m_performance=0&min_6m_performance=0&max_price=10000"
```

## 🔍 Frontend Debugging Steps

### 1. Check API Response

Open browser console and run:
```javascript
fetch('/midas/asset/available_sectors')
  .then(r => r.json())
  .then(data => {
    console.log('All sectors:', data);
    console.log('tech_sic:', data.tech_sic);
    console.log('tech_sic available:', data.tech_sic?.available);
  });
```

**Expected Output:**
- `tech_sic` should exist in the response
- `tech_sic.available` should be `true`
- `tech_sic.name` should be `"Technology/AI"`

### 2. Check Dropdown Filtering Logic

If your frontend filters sectors, ensure it includes `tech_sic`:

```javascript
// ✅ CORRECT: Include tech_sic
const allowedSectors = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];

// ❌ WRONG: Missing tech_sic
const allowedSectors = ['universe', 'all', 'tech', 'energy', 'healthcare'];
```

### 3. Check Dropdown Rendering

Verify the dropdown is rendering all allowed sectors:

```javascript
// Example React component check
useEffect(() => {
  fetch('/midas/asset/available_sectors')
    .then(r => r.json())
    .then(data => {
      const allowed = ['universe', 'all', 'tech_sic', 'energy_sic', 'healthcare_sic'];
      const sectors = Object.entries(data)
        .filter(([key]) => allowed.includes(key))
        .map(([key, sector]) => ({ ...sector, value: key }));
      
      console.log('Filtered sectors for dropdown:', sectors);
      setSectors(sectors);
    });
}, []);
```

### 4. Check Sector Selection

When user selects a sector, verify the correct value is sent:

```javascript
const handleSectorChange = (value) => {
  console.log('Selected sector value:', value); // Should be "tech_sic", not "tech"
  
  fetch(`/midas/asset/stock_screener?sector=${value}`)
    .then(r => r.json())
    .then(data => {
      console.log('Screener results:', data);
    });
};
```

### 5. Common Issues

#### Issue 1: Frontend filtering out `tech_sic`
**Symptom:** Dropdown doesn't show "Technology/AI"
**Fix:** Check if frontend filters by `type === "sic_based"` or includes `tech_sic` in allowed list

#### Issue 2: Wrong sector value sent
**Symptom:** Dropdown shows option but selecting it doesn't work
**Fix:** Ensure `value="tech_sic"` (not `value="tech"`) is sent to API

#### Issue 3: Empty results
**Symptom:** Sector selected but no results returned
**Fix:** Default filters are strict (10% 1M, 20% 3M, 30% 6M, max $50). Relax filters or check if stocks meet criteria.

## 📋 Frontend Implementation Checklist

- [ ] Fetching from `/midas/asset/available_sectors`
- [ ] Filtering to include: `universe`, `all`, `tech_sic`, `energy_sic`, `healthcare_sic`
- [ ] Using `sector.name` for display text ("Technology/AI")
- [ ] Using `sector.value` for API calls ("tech_sic")
- [ ] Not filtering by `available: true` (all SIC sectors should be available)
- [ ] Sending correct `sector` parameter to `/midas/asset/stock_screener`

## 🧪 Quick Test

Run this in browser console to test the full flow:

```javascript
// 1. Get sectors
const sectors = await fetch('/midas/asset/available_sectors').then(r => r.json());
console.log('tech_sic in response:', 'tech_sic' in sectors);

// 2. Test screener with tech_sic
const results = await fetch('/midas/asset/stock_screener?sector=tech_sic&limit=3&min_1m_performance=0&min_3m_performance=0&min_6m_performance=0&max_price=10000').then(r => r.json());
console.log('Screener results count:', results.length);
console.log('First result:', results[0]);
```

If both steps work, the backend is fine and the issue is in frontend dropdown rendering/filtering.
