# Automatic Checkpoint/Resume Stock Screener

## Overview

The stock screener **automatically** handles checkpointing and resume capability. No configuration needed - it just works! If a scan is interrupted, simply call the endpoint again and it will automatically resume from where it left off.

## Key Features

✅ **Automatic Checkpointing**: Progress saved every 50 tickers (no configuration needed)  
✅ **Auto-Resume**: Automatically detects and resumes from last checkpoint  
✅ **Incremental Caching**: Cache saved as you go (not just at end)  
✅ **Interruption Safe**: Can stop and restart without losing progress  
✅ **Smart Filter Matching**: Only resumes if filters match previous run  
✅ **Cache First**: Uses cache when available, only fetches new data when needed  

## How It Works

### Checkpoint System

1. **Checkpoint File**: `cache/screener_checkpoint.json`
   - Stores which tickers have been processed
   - Tracks statistics (cached, fetched, failed counts)
   - Includes filter hash to ensure compatibility

2. **Checkpoint Frequency**: Every 50 tickers processed

3. **Auto-Resume**: Automatically detects and resumes from checkpoint

### Process Flow

```
1. Start Screening (batch_mode=true)
   ↓
2. Check for checkpoint
   ↓
3. If checkpoint exists:
   - Verify filters match
   - Skip already-processed tickers
   - Resume from where it stopped
   ↓
4. Process tickers
   ↓
5. Every 50 tickers:
   - Save checkpoint
   - Save cache incrementally
   ↓
6. When complete:
   - Clear checkpoint
   - Save final cache
```

## Usage

### It's Automatic!

**No configuration needed** - checkpointing and resume work automatically!

```python
# Via API - just call normally!
GET /midas/asset/stock_screener?sector=all&limit=50

# First call: Starts processing
# If interrupted, same call automatically resumes!
```

### How It Works

1. **First Call**: Starts processing all tickers
2. **Checkpoint Saved**: Every 50 tickers automatically
3. **If Interrupted**: Just call the same endpoint again
4. **Auto-Resume**: Automatically detects checkpoint and resumes
5. **When Complete**: Checkpoint cleared automatically

### Example API Calls

#### Start or Resume Scan
```bash
# Start new scan or resume if interrupted - same call!
curl "http://localhost:8000/midas/asset/stock_screener?sector=all&limit=50"
```

**That's it!** The system automatically:
- ✅ Checks for existing checkpoint
- ✅ Resumes if checkpoint found and filters match
- ✅ Starts fresh if no checkpoint or filters changed
- ✅ Uses cache when available
- ✅ Only fetches new data when needed

#### Clear Checkpoint (Start Fresh)

If you want to force a fresh start (ignore checkpoint):

```python
from services.stock_screener_service import clear_checkpoint
clear_checkpoint()
```

## Checkpoint File Format

```json
{
  "timestamp": "2024-10-25T12:00:00",
  "batch_id": "20241025_120000",
  "filters_hash": "a1b2c3d4",
  "processed_tickers": ["AAPL", "MSFT", "GOOGL", ...],
  "stats": {
    "cached_count": 500,
    "fetched_count": 2000,
    "failed_count": 10
  }
}
```

## Example Scenario

### Scenario: Processing 11,802 Tickers

**Initial Run:**
```bash
# Start batch processing
GET /midas/asset/stock_screener?batch_mode=true&sector=all

# Processing 0/11802...
# Processing 1000/11802...
# Processing 5000/11802...
# 💾 Checkpoint saved: 5000 tickers processed
# [INTERRUPTED - Server crash, network issue, etc.]
```

**Resume Run:**
```bash
# Same call automatically resumes
GET /midas/asset/stock_screener?batch_mode=true&sector=all

# 📋 RESUMING: 5000 tickers already processed
# ⏭️ Skipping 5000 already processed tickers
# 📊 Remaining to process: 6802 / 11802
# Processing 6802/11802...
# Processing 11802/11802...
# ✅ BATCH COMPLETE - All tickers processed!
```

## Benefits

### Time Savings
- **Before**: 60 minutes lost if interrupted at 50 minutes
- **After**: Resume from minute 50, only lose 10 minutes

### Reliability
- Handle server crashes gracefully
- Survive network interruptions
- Recover from API rate limits

### Progress Tracking
- Know exactly where you stopped
- See statistics at each checkpoint
- Monitor progress over time

## Configuration

### Checkpoint Interval

Currently set to **50 tickers**. To change:

```python
# In stock_screener_service.py
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N tickers
```

### Cache Duration

Checkpoints expire after cache duration (12 hours by default):

```python
CACHE_DURATION_HOURS = 12
```

## Manual Checkpoint Management

### Check Checkpoint Status
```python
from services.stock_screener_service import load_checkpoint
checkpoint = load_checkpoint()
if checkpoint:
    print(f"Processed: {len(checkpoint['processed_tickers'])} tickers")
    print(f"Stats: {checkpoint['stats']}")
```

### Clear Checkpoint
```python
from services.stock_screener_service import clear_checkpoint
clear_checkpoint()  # Start fresh next time
```

### Force New Batch
```python
# Via API
GET /midas/asset/stock_screener?batch_mode=true&resume=false
```

## Logging

Batch mode provides detailed logging:

```
================================================================================
🔄 BATCH MODE ENABLED
================================================================================
📋 RESUMING: 5000 tickers already processed
📊 Stats from checkpoint: Cached=500, Fetched=4500, Failed=10
⏭️ Skipping 5000 already processed tickers
📊 Remaining to process: 6802 / 11802
...
💾 Checkpoint saved: 5050 tickers processed, 50 new items cached
...
✅ BATCH COMPLETE - All tickers processed!
🗑️ Checkpoint cleared (batch complete)
```

## Best Practices

1. **It's Always On**: Checkpointing works automatically - no setup needed!

2. **Keep Same Filters**: Don't change filters mid-scan (checkpoint won't match)

3. **Monitor Progress**: Check logs to see checkpoint saves and resume status

4. **Complete the Scan**: Let it finish to clear checkpoint automatically

5. **Call Again to Resume**: If interrupted, just call the same endpoint again

6. **Clear if Needed**: If you change filters, clear checkpoint first

## Troubleshooting

### Checkpoint Not Resuming

**Problem**: Checkpoint exists but not resuming

**Solution**: 
- Verify filters match exactly
- Check checkpoint file exists: `cache/screener_checkpoint.json`
- Set `resume=false` to start fresh

### Checkpoint Expired

**Problem**: Checkpoint older than cache duration

**Solution**:
- Checkpoint auto-expires after 12 hours
- Start new batch (old checkpoint ignored)

### Wrong Tickers Processed

**Problem**: Resuming but wrong tickers being skipped

**Solution**:
- Clear checkpoint: `clear_checkpoint()`
- Start fresh with `resume=false`

## Performance Impact

- **Checkpoint Save**: ~10-50ms per checkpoint (negligible)
- **Checkpoint Load**: ~5-10ms on startup (negligible)
- **Incremental Cache**: Saves as you go (better than all-at-end)

**Net Result**: Minimal overhead, huge reliability gain!

## Summary

The stock screener now automatically handles checkpointing and resume - **no configuration needed**! Perfect for:

- ✅ Large universe scans (11,000+ tickers)
- ✅ Long-running processes (60+ minutes)
- ✅ Unreliable environments (network issues, server restarts)
- ✅ Testing/debugging (can stop/resume easily)

**Just call the endpoint** - it automatically:
- ✅ Checks for progress
- ✅ Resumes if interrupted
- ✅ Uses cache efficiently
- ✅ Only fetches new data when needed

**No flags, no configuration - it just works!** 🎉

