# How Sampling Works in Stock Screener

## Current Implementation

The sampling logic in `services/stock_screener_service.py` uses **systematic sampling** with **randomization**.

### Code Flow

```python
# Line 287-290
sample_size = min(sample_size, total)  # Ensure we don't exceed total
step = max(1, total // sample_size)    # Calculate step size
tickers = [all_tickers[i] for i in range(0, total, step)][:sample_size]
random.shuffle(tickers)                # Randomize the order
```

### Step-by-Step Process

#### Example with 11,802 tickers, sample_size = 3,000

1. **Calculate Step Size**
   ```
   step = max(1, 11,802 // 3,000)
   step = max(1, 3)
   step = 3
   ```

2. **Systematic Sampling**
   ```
   Take every 3rd ticker: [0, 3, 6, 9, 12, ...]
   This gives: 11,802 / 3 = 3,934 tickers
   ```

3. **Limit to Sample Size**
   ```
   [:sample_size] → First 3,000 tickers from the sampled list
   ```

4. **Random Shuffle**
   ```
   random.shuffle(tickers)
   Randomizes the order (but keeps the same 3,000 tickers)
   ```

### Visual Representation

```
All Tickers (11,802 total):
[A, B, C, D, E, F, G, H, I, J, K, L, ...]

Step 1: Take every 3rd ticker
[A, _, _, D, _, _, G, _, _, J, _, _, ...]
 ↓     ↓     ↓     ↓     ↓     ↓
[0]   [3]   [6]   [9]   [12]  [15]

Step 2: Limit to 3,000
Keep first 3,000 from the sampled list

Step 3: Shuffle
Randomize the order of those 3,000 tickers
```

## Characteristics

### Advantages ✅
- **Fast**: O(n) complexity, very efficient
- **Distributed**: Every 3rd ticker ensures even distribution across the list
- **Deterministic**: Same tickers selected each time (before shuffle)
- **Randomized Order**: Shuffle prevents bias from original list order

### Potential Issues ⚠️

1. **Not True Random Sampling**
   - Uses systematic sampling (every Nth ticker)
   - If tickers are ordered in some pattern, might introduce bias

2. **Step Calculation Limitation**
   - With 11,802 tickers and step=3, we get 3,934 tickers
   - Only first 3,000 are used
   - Last ~934 systematically sampled tickers are discarded

3. **Alphabetical Bias**
   - If tickers are stored alphabetically, sampling every 3rd gives:
     - Good coverage across A-Z
     - But misses patterns (e.g., all tickers starting with same letter might be skipped)

## How It Actually Works in Practice

### Real Example

```python
total_tickers = 11802
sample_size = 3000
step = 3

# Selected indices: [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, ...]
# After [:3000] limit: First 3,000 indices
# After shuffle: Same tickers, random order
```

### Coverage

- **Total Tickers**: 11,802
- **Sampled**: 3,000 (25.4% of universe)
- **Distribution**: Every 3rd ticker, evenly spaced
- **Coverage**: Spreads across entire ticker list

## Alternative Sampling Strategies

### Option 1: True Random Sampling
```python
import random
tickers = random.sample(all_tickers, min(sample_size, len(all_tickers)))
```
**Pros**: True randomness, no systematic bias  
**Cons**: Slower (O(n) for sample operation), less predictable

### Option 2: Stratified by Alphabet
```python
# Group tickers by first letter
tickers_by_letter = {}
for ticker in all_tickers:
    first_letter = ticker[0].upper()
    if first_letter not in tickers_by_letter:
        tickers_by_letter[first_letter] = []
    tickers_by_letter[first_letter].append(ticker)

# Sample evenly from each letter
samples_per_letter = sample_size // len(tickers_by_letter)
sampled_tickers = []
for letter_tickers in tickers_by_letter.values():
    sampled_tickers.extend(random.sample(letter_tickers, min(samples_per_letter, len(letter_tickers))))
```
**Pros**: Guaranteed coverage across all letters  
**Cons**: More complex, might not sample evenly if some letters have few tickers

### Option 3: Stratified by Market Cap/Volume
```python
# Sort by market cap or volume
sorted_tickers = sort_by_market_cap(all_tickers)
# Then sample from different tiers (large, mid, small cap)
```
**Pros**: Ensures coverage across market segments  
**Cons**: Requires additional data/sorting

## Current Behavior Summary

1. **Deterministic Selection**: Same tickers chosen (systematic sampling)
2. **Random Order**: Final order is randomized
3. **Even Distribution**: Spreads across entire ticker list
4. **Efficient**: Fast O(n) operation
5. **Configurable**: Can adjust `sample_size` parameter

## Configuration

### Default Settings
- `sample_size = 3000` (from filters or default)
- `use_full_universe = False` (samples by default)

### To Use Full Universe
```python
filters = {
    "use_full_universe": True,  # Process all 11,802 tickers
    # ... other filters
}
```

### To Adjust Sample Size
```python
filters = {
    "sample_size": 5000,  # Sample 5,000 tickers instead of 3,000
    # ... other filters
}
```

## Recommendation

The current sampling works well for most use cases:
- ✅ Efficient and fast
- ✅ Good distribution across ticker universe
- ✅ Configurable sample size
- ✅ Randomized order prevents bias

**For most users**: Current sampling is sufficient. Use `use_full_universe=True` only when you need complete coverage.

