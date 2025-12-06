# Stock Screener Frontend/Backend Analysis

## Issues Found

### 1. **Filter Parameter Mismatches**

**Frontend sends (but backend ignores):**
- ❌ `max_1m_performance` - Backend doesn't filter by max performance
- ❌ `max_3m_performance` - Backend doesn't filter by max performance  
- ❌ `max_6m_performance` - Backend doesn't filter by max performance
- ❌ `min_adr` - Backend doesn't filter by ADR
- ❌ `max_adr` - Backend doesn't filter by ADR
- ❌ `sort_by` - Backend always sorts by ADR descending
- ❌ `sort_order` - Backend always sorts by ADR descending

**Backend expects (but frontend doesn't send):**
- ❌ `rsi_signal` - Frontend doesn't provide this filter option

### 2. **Filtering Logic Issues**

**Backend filtering:**
```python
# Only checks >= min, no max checks
if (stock_data["current_price"] >= min_price and 
    stock_data["current_price"] <= max_price and
    stock_data["performance_1m"] >= min_1m and  # No max check!
    stock_data["performance_3m"] >= min_3m and  # No max check!
    stock_data["performance_6m"] >= min_6m and  # No max check!
    rsi >= min_rsi and
    rsi <= max_rsi and
    rsi_signal_match):
```

**Missing filters:**
- No ADR filtering (min_adr, max_adr)
- No max performance filtering

### 3. **Sorting**

**Backend:** Always sorts by `adr_percentage` descending (hardcoded)
**Frontend:** Expects configurable sorting by:
- `adr` | `rsi` | `performance_1m` | `performance_3m` | `performance_6m`
- `asc` | `desc`

### 4. **Data Format**

✅ Response format appears to match (both use same structure)

## Recommendations

### Option 1: Update Backend to Match Frontend (Recommended)
- Add max performance filters
- Add ADR filters
- Add configurable sorting
- Add rsi_signal to frontend UI

### Option 2: Update Frontend to Match Backend
- Remove max performance filters
- Remove ADR filters  
- Remove sort controls (backend always sorts by ADR)
- Remove unused filter inputs

### Option 3: Hybrid Approach
- Keep essential filters (price, performance min, RSI)
- Add missing backend features (max performance, ADR filtering, sorting)
- Add rsi_signal filter to frontend

