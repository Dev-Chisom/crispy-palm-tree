# SignalIQ Backend - Expected Behavior

## 🎯 System Overview

SignalIQ is an AI-powered investment intelligence platform that:
- Fetches stock data from Yahoo Finance (US and NGX markets)
- Generates BUY/HOLD/SELL signals with confidence scores
- Provides explainable AI reasoning for each recommendation
- Updates data automatically via scheduled background jobs

---

## 📊 Core Workflows

### 1. Adding a Stock (POST /api/v1/stocks)

**User Action:**
```json
POST /api/v1/stocks
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "market": "US",
  "sector": "Technology"
}
```

**Expected Behavior:**
1. ✅ **Immediate Response** (< 1 second)
   - Stock is created in database
   - Returns stock object with ID
   - Status: 201 Created

2. 🔄 **Background Tasks Queued** (Automatic, Non-blocking)
   - `fetch_stock_prices(symbol, market)` - Queued immediately
   - `update_fundamentals(symbol)` - Queued immediately
   - `calculate_indicators(symbol)` - Queued immediately
   - All tasks run in parallel (except indicators wait for prices)

3. 📈 **Data Fetching Process** (5-20 seconds)
   - **Prices Task:**
     - Fetches 1 year of OHLCV data from Yahoo Finance
     - Stores ~252 trading days in database
     - Time: 3-18 seconds
   
   - **Fundamentals Task:**
     - Fetches P/E ratio, EPS, Revenue, Debt Ratio, Earnings Growth
     - Stores in database
     - Time: 2-12 seconds
   
   - **Indicators Task:**
     - Waits for prices to complete
     - Calculates RSI, MACD, SMAs, Bollinger Bands, etc.
     - Stores latest indicators in database
     - Time: 2-4 seconds

4. ✅ **Result:**
   - Stock exists in database
   - Price data available
   - Fundamentals available
   - Technical indicators calculated
   - Ready for signal generation

---

### 2. Getting a Signal (GET /api/v1/signals/{symbol}/signal)

**User Action:**
```
GET /api/v1/signals/AAPL/signal
```

**Expected Behavior:**

1. ✅ **Check Cache** (< 0.1 seconds)
   - If signal exists in Redis cache and is fresh (< 1 hour old)
   - Return cached signal immediately
   - Status: 200 OK with `cache_hit: true`

2. 🔍 **Check Database** (< 0.5 seconds)
   - If no cache, check for latest signal in database
   - If signal exists and is fresh (< 1 hour old)
   - Cache it and return
   - Status: 200 OK with `cache_hit: false`

3. 🧠 **Generate New Signal** (< 2 seconds)
   - If no signal or signal is stale:
     - Fetch price data (from DB or Yahoo Finance)
     - Get technical indicators (from DB or calculate)
     - Get fundamentals (from DB or Yahoo Finance)
     - Calculate composite score:
       - Technical Analysis (40%): RSI, MACD, Moving Averages, Bollinger Bands
       - Fundamental Analysis (30%): P/E, EPS, Revenue, Debt Ratio
       - Trend Analysis (20%): Short/medium/long-term trends
       - Volatility & Risk (10%): Historical volatility, drawdown
     - Determine signal type:
       - BUY: Score > 60, positive momentum
       - HOLD: Score 40-60, mixed signals
       - SELL: Score < 40, negative momentum
       - NO_SIGNAL: Insufficient data or conflicting signals
     - Generate explanation (why this signal?)
     - Store signal in database
     - Cache for 1 hour
   - Status: 200 OK

4. ✅ **Response Format:**
```json
{
  "data": {
    "signal_type": "BUY",
    "confidence_score": 75,
    "risk_level": "MEDIUM",
    "holding_period": "MEDIUM_TERM",
    "explanation": "Strong upward momentum with RSI below overbought zone...",
    "stock": {...}
  },
  "meta": {
    "timestamp": "2026-02-03T21:00:00Z",
    "cache_hit": false
  }
}
```

---

### 3. Getting Top Recommendations (GET /api/v1/signals/top)

**User Action:**
```
GET /api/v1/signals/top?market=US&signal_type=BUY&limit=10
```

**Expected Behavior:**

1. ✅ **Check Cache** (< 0.1 seconds)
   - If top signals cached (15 minutes TTL)
   - Return cached results immediately

2. 🔍 **Query Database** (< 1 second)
   - Filter by market (US or NGX)
   - Filter by signal_type (BUY, HOLD, SELL)
   - Get today's signals only
   - Order by confidence_score (descending)
   - Limit to requested number (default: 10, max: 100)

3. ✅ **Response:**
```json
{
  "data": {
    "items": [
      {
        "signal_type": "BUY",
        "confidence_score": 85,
        "stock": {"symbol": "AAPL", "name": "Apple Inc."},
        ...
      },
      ...
    ],
    "total": 10
  },
  "meta": {
    "timestamp": "2026-02-03T21:00:00Z",
    "cache_hit": false
  }
}
```

---

### 4. Scheduled Background Jobs (Automatic)

**Celery Beat Scheduler** runs these tasks automatically:

#### A. Daily Price Updates
- **Schedule:** 9:30 PM UTC daily (4:30 PM EST - after US market close)
- **Task:** `update_all_stock_prices`
- **Behavior:**
  - Gets all active stocks from database
  - Queues `fetch_stock_prices` task for each stock
  - Updates price data for all stocks
  - Runs in parallel (Celery handles concurrency)

#### B. Weekly Fundamentals Refresh
- **Schedule:** Sunday at midnight UTC
- **Task:** `update_all_fundamentals`
- **Behavior:**
  - Gets all active stocks
  - Queues `update_fundamentals` task for each stock
  - Updates P/E, EPS, Revenue, etc.
  - Runs in parallel

#### C. Hourly Indicator Recalculation
- **Schedule:** Every hour at :00 (e.g., 1:00, 2:00, 3:00)
- **Task:** `recalculate_all_indicators`
- **Behavior:**
  - Gets all active stocks
  - Queues `calculate_indicators` task for each stock
  - Recalculates RSI, MACD, SMAs, etc.
  - Keeps indicators fresh throughout the day

---

## 🔄 Data Flow Diagram

```
User Creates Stock
    ↓
POST /api/v1/stocks
    ↓
Stock Created in DB (< 1s)
    ↓
3 Background Tasks Queued:
    ├─ fetch_stock_prices() ────┐
    ├─ update_fundamentals() ───┤ (Parallel)
    └─ calculate_indicators() ───┘ (Waits for prices)
    ↓
Yahoo Finance API Calls
    ↓
Data Stored in Database
    ↓
Ready for Signal Generation
    ↓
GET /api/v1/signals/{symbol}/signal
    ↓
Signal Generated (< 2s)
    ↓
Stored in DB + Cached in Redis
```

---

## 📋 Key Behaviors to Confirm

### ✅ Automatic Data Fetching
- When a stock is created, data fetching happens automatically in background
- No manual trigger needed
- Tasks run asynchronously (non-blocking)

### ✅ Signal Generation
- Signals are generated on-demand when requested
- Uses cached data if available (< 1 hour old)
- Falls back to Yahoo Finance if DB data is missing
- Generation time: < 2 seconds

### ✅ Scheduled Updates
- Daily price updates after market close
- Weekly fundamentals refresh
- Hourly indicator recalculation
- All run automatically via Celery Beat

### ✅ Caching Strategy
- Signals: 1 hour TTL
- Prices: 5 minutes TTL
- Fundamentals: 24 hours TTL
- Top signals: 15 minutes TTL

### ✅ Error Handling
- Yahoo Finance timeouts: 10 seconds per call
- Retry logic: 3 attempts for prices, 2 for fundamentals
- Exponential backoff: 2^attempt seconds
- Graceful degradation: Falls back to DB data if API fails

### ✅ Data Availability
- US stocks: Full support via Yahoo Finance
- NGX stocks: Supported via Yahoo Finance (SYMBOL.NG format)
- Fundamentals: May be limited for NGX stocks

---

## 🎯 Expected User Experience

### Scenario 1: New User Adds First Stock
1. User: `POST /api/v1/stocks` → Gets immediate response
2. System: Background tasks fetch data (5-20 seconds)
3. User: `GET /api/v1/signals/AAPL/signal` → Gets signal (< 2 seconds)
4. Result: User sees BUY/HOLD/SELL recommendation with explanation

### Scenario 2: User Checks Top Recommendations
1. User: `GET /api/v1/signals/top?signal_type=BUY&limit=10`
2. System: Returns top 10 BUY signals sorted by confidence
3. Time: < 2 seconds (cached or from DB)
4. Result: User sees best stocks to buy right now

### Scenario 3: Data Auto-Updates
1. System: Daily at 9:30 PM UTC, updates all stock prices
2. System: Hourly, recalculates all indicators
3. System: Weekly, refreshes fundamentals
4. User: Always sees fresh data without manual refresh

---

## ⚠️ Important Notes

1. **First-Time Data Fetch:** Takes 5-20 seconds (Yahoo Finance API)
2. **Subsequent Requests:** < 2 seconds (cached or from DB)
3. **Signal Generation:** Always < 2 seconds (requirement met)
4. **Background Jobs:** Run automatically, no user action needed
5. **Celery Workers:** Must be running for background tasks to execute
6. **Redis:** Required for caching and Celery broker

---

## 🔍 Verification Checklist

- [ ] Stock creation returns immediately (< 1 second)
- [ ] Background tasks are queued automatically
- [ ] Data appears in database within 5-20 seconds
- [ ] Signal generation takes < 2 seconds
- [ ] Top signals endpoint returns sorted by confidence
- [ ] Scheduled tasks run at correct times
- [ ] Caching works (faster on second request)
- [ ] Error handling works (retries, fallbacks)

---

## 📞 Questions to Confirm

1. ✅ Is automatic data fetching on stock creation expected?
2. ✅ Is 5-20 seconds acceptable for initial data fetch?
3. ✅ Is < 2 seconds for signal generation acceptable?
4. ✅ Are scheduled updates (daily/weekly/hourly) expected?
5. ✅ Should signals be cached for 1 hour?
6. ✅ Should top signals be sorted by confidence score?
