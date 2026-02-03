# Frontend Requirements - Growth/Dividend Classification

## 📊 New Data Fields Available

### 1. Stock Classification (`stock_type`)
**Location:** Stock object
**Values:** `"GROWTH"` | `"DIVIDEND"` | `"HYBRID"` | `null`

```json
{
  "id": 1,
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "stock_type": "GROWTH",  // ← NEW
  ...
}
```

### 2. Dividend Information
**Location:** Fundamentals object
**New Fields:**
- `dividend_yield` (float, percentage) - Annual dividend yield
- `dividend_per_share` (float) - Annual dividend per share
- `dividend_payout_ratio` (float, percentage) - Percentage of earnings paid as dividends

```json
{
  "id": 1,
  "stock_id": 1,
  "dividend_yield": 2.5,        // ← NEW
  "dividend_per_share": 0.96,   // ← NEW
  "dividend_payout_ratio": 15.2, // ← NEW
  ...
}
```

### 3. Signal Explanation - Stock Classification
**Location:** Signal response → `explanation.stock_classification`

```json
{
  "signal_type": "BUY",
  "confidence_score": 75,
  "holding_period": "LONG",
  "explanation": {
    "summary": "...",
    "stock_classification": {  // ← NEW
      "stock_type": "GROWTH",
      "investor_recommendation": {
        "best_for": [
          "Growth investors",
          "Long-term wealth building",
          "Capital appreciation seekers"
        ],
        "strategy": "Focus on capital gains and reinvestment",
        "time_horizon": "Long-term (5+ years)",
        "action": "Consider adding to growth portfolio"
      }
    }
  }
}
```

---

## 🎨 Frontend Display Requirements

### 1. Stock Detail Page

#### A. Stock Type Badge
**Location:** Near stock name/symbol
**Display:**
- **GROWTH**: Green badge with "Growth Stock" or growth icon
- **DIVIDEND**: Blue badge with "Dividend Stock" or dividend icon
- **HYBRID**: Purple badge with "Hybrid Stock" or combined icon
- **null**: No badge (not yet classified)

**Example:**
```
AAPL - Apple Inc.  [GROWTH] ← Badge here
```

#### B. Dividend Information Card
**Location:** In fundamentals section
**Display when `dividend_yield` exists:**

```
┌─────────────────────────────┐
│ Dividend Information         │
├─────────────────────────────┤
│ Dividend Yield: 2.5%         │
│ Dividend per Share: $0.96    │
│ Payout Ratio: 15.2%          │
└─────────────────────────────┘
```

**Display when no dividend:**
```
No dividend information available
```

### 2. Signal Display

#### A. Investor Recommendation Section
**Location:** In signal explanation card
**Display:**

```
┌─────────────────────────────────────┐
│ Investment Recommendation           │
├─────────────────────────────────────┤
│ Stock Type: GROWTH                  │
│                                     │
│ Best For:                           │
│ • Growth investors                 │
│ • Long-term wealth building        │
│ • Capital appreciation seekers     │
│                                     │
│ Strategy:                           │
│ Focus on capital gains and          │
│ reinvestment                        │
│                                     │
│ Time Horizon:                       │
│ Long-term (5+ years)                │
│                                     │
│ Action:                             │
│ Consider adding to growth portfolio │
└─────────────────────────────────────┘
```

### 3. Stock List/Table

#### A. Add Stock Type Column
**Display:**
- Column header: "Type"
- Show badge/icon for each stock type
- Sortable/filterable by stock type

#### B. Filter by Stock Type
**Add filter options:**
- "All Stocks"
- "Growth Stocks"
- "Dividend Stocks"
- "Hybrid Stocks"

### 4. Top Signals Page

#### A. Group by Stock Type
**Option 1:** Tabs
```
[All] [Growth] [Dividend] [Hybrid]
```

**Option 2:** Sections
```
Top Growth Stocks
Top Dividend Stocks
Top Hybrid Stocks
```

#### B. Show Stock Type in Signal Card
**Display stock type badge on each signal card**

---

## 🎯 User Experience Enhancements

### 1. Investor Profile Selection
**Add user preference:**
- "I'm a Growth Investor"
- "I'm a Dividend Investor"
- "I'm a Balanced Investor"

**Then:**
- Highlight stocks matching their profile
- Show personalized recommendations
- Filter signals by investor type

### 2. Comparison View
**Allow users to compare:**
- Growth stocks vs Dividend stocks
- Show side-by-side metrics
- Highlight differences

### 3. Portfolio Builder
**Help users build portfolios:**
- "Build Growth Portfolio"
- "Build Dividend Portfolio"
- "Build Balanced Portfolio"

---

## 📱 API Endpoints to Use

### 1. Get Stock with Classification
```
GET /api/v1/stocks/{symbol}
```
**Response includes:** `stock_type` field

### 2. Get Fundamentals with Dividends
```
GET /api/v1/stocks/{symbol}/fundamentals
```
**Response includes:** `dividend_yield`, `dividend_per_share`, `dividend_payout_ratio`

### 3. Get Signal with Recommendations
```
GET /api/v1/stocks/{symbol}/signal
```
**Response includes:** `explanation.stock_classification` with investor recommendations

### 4. Filter Stocks by Type
```
GET /api/v1/stocks?stock_type=GROWTH
GET /api/v1/stocks?stock_type=DIVIDEND
GET /api/v1/stocks?stock_type=HYBRID
```

---

## 🎨 Visual Design Suggestions

### Colors
- **GROWTH**: Green (#10B981) - represents growth/upward trend
- **DIVIDEND**: Blue (#3B82F6) - represents stability/income
- **HYBRID**: Purple (#8B5CF6) - represents combination

### Icons
- **GROWTH**: 📈 Chart trending up
- **DIVIDEND**: 💰 Money/Dollar sign
- **HYBRID**: ⚖️ Balance scale or combined icon

### Badges
- Small, rounded badges
- Icon + text
- Subtle background color
- Hover tooltip with explanation

---

## ✅ Implementation Checklist

- [ ] Add `stock_type` field to stock display
- [ ] Add dividend information card to fundamentals section
- [ ] Add investor recommendation section to signal display
- [ ] Add stock type filter to stock list
- [ ] Add stock type column to stock table
- [ ] Add stock type badge to signal cards
- [ ] Group top signals by stock type
- [ ] Add investor profile selection (optional)
- [ ] Add comparison view (optional)
- [ ] Add portfolio builder (optional)

---

## 📝 Example API Response

### Stock Response
```json
{
  "data": {
    "id": 1,
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "market": "US",
    "sector": "Technology",
    "stock_type": "GROWTH",
    "currency": "USD",
    "is_active": true
  }
}
```

### Fundamentals Response
```json
{
  "data": {
    "id": 1,
    "stock_id": 1,
    "dividend_yield": 0.5,
    "dividend_per_share": 0.24,
    "dividend_payout_ratio": 15.2,
    "pe_ratio": 28.5,
    "earnings_growth": 12.5
  }
}
```

### Signal Response
```json
{
  "data": {
    "signal_type": "BUY",
    "confidence_score": 75,
    "holding_period": "LONG",
    "explanation": {
      "summary": "BUY - Strong upward momentum...",
      "stock_classification": {
        "stock_type": "GROWTH",
        "investor_recommendation": {
          "best_for": [
            "Growth investors",
            "Long-term wealth building"
          ],
          "strategy": "Focus on capital gains",
          "time_horizon": "Long-term (5+ years)",
          "action": "Consider adding to growth portfolio"
        }
      }
    }
  }
}
```

---

## 🚀 Next Steps

1. **Backend is ready** - All data is available via API
2. **Frontend should:**
   - Update stock display components
   - Add dividend information display
   - Add investor recommendation section
   - Add filtering/grouping by stock type
3. **Test with real data** - Create stocks and verify classification
4. **User feedback** - Gather feedback on UI/UX
