# 🎨 Frontend Update Guide - Investment Signals

## 📋 Overview

The backend now generates **INVESTMENT signals** (not trading signals) optimized for:
- Long-term investing
- Dividend-focused analysis
- Investment timing (when to buy, how long to hold, when to sell)

---

## 🔄 API Response Changes

### Signal Response Structure

The signal response now includes **investment-focused** data:

```json
{
  "data": {
    "id": 123,
    "stock_id": 1,
    "signal_type": "BUY",
    "confidence_score": 75.5,
    "risk_level": "LOW",
    "holding_period": "LONG",
    "created_at": "2026-02-03T12:00:00Z",
    "explanation": {
      "summary": "BUY signal for long-term investing with 75.5% confidence",
      "investment_focus": true,  // ← NEW: Indicates investment-focused signal
      
      "factors": {
        "dividend": {  // ← NEW: Dividend analysis section
          "score": 75,
          "dividend_yield": 3.5,
          "dividend_per_share": 2.50,
          "dividend_payout_ratio": 45.2,
          "is_dividend_stock": true
        },
        "fundamental": {
          "score": 80,
          "pe_ratio": 18.5,
          "earnings_growth": 12.3,
          "debt_ratio": 35.0
        },
        "long_term_trend": {
          "score": 70,
          "factors": [
            "Strong long-term uptrend (25.3% over 6 months)",
            "Low volatility (18.2%) - stable for long-term holding"
          ]
        },
        "entry_timing": {  // ← NEW: Entry timing guidance
          "score": 65,
          "timing": "GOOD"  // "GOOD" | "FAIR" | "WAIT"
        }
      },
      
      "investment_guidance": {  // ← NEW: Investment guidance section
        "when_to_buy": "GOOD",  // Entry timing
        "how_long_to_hold": "LONG",  // Holding period
        "when_to_sell": "If fundamentals deteriorate or dividend is cut"
      },
      
      "triggers": [
        "High dividend yield (3.5%) - excellent for income",
        "Sustainable payout ratio (45.2%) - healthy balance",
        "Strong earnings growth (12.3%) - dividend may increase"
      ],
      
      "risks": [
        "Debt ratio: 35.0%",
        "Dividend payout: 45.2%"
      ]
    }
  }
}
```

---

## 🎨 UI Components to Update

### 1. Signal Card/Display Component

#### Current Display (Trading-focused):
```
[BUY] Confidence: 75% | Risk: LOW | Hold: LONG
```

#### New Display (Investment-focused):
```
┌─────────────────────────────────────────────┐
│ 🎯 BUY Signal (Investment)                  │
│ Confidence: 75% | Risk: LOW | Hold: LONG    │
├─────────────────────────────────────────────┤
│ 💰 Dividend Yield: 3.5%                     │
│ 📈 Entry Timing: GOOD                        │
│ ⏱️  Hold Period: LONG (5+ years)            │
│                                             │
│ Investment Guidance:                        │
│ • When to Buy: GOOD entry timing           │
│ • How Long to Hold: LONG                    │
│ • When to Sell: If fundamentals deteriorate │
└─────────────────────────────────────────────┘
```

**Code Example:**
```tsx
// SignalCard.tsx
interface SignalData {
  signal_type: "BUY" | "HOLD" | "SELL" | "NO_SIGNAL";
  confidence_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  holding_period: "SHORT" | "MEDIUM" | "LONG";
  explanation: {
    investment_focus?: boolean;
    factors: {
      dividend?: {
        dividend_yield?: number;
        dividend_per_share?: number;
        is_dividend_stock?: boolean;
      };
      entry_timing?: {
        timing: "GOOD" | "FAIR" | "WAIT";
      };
    };
    investment_guidance?: {
      when_to_buy: string;
      how_long_to_hold: string;
      when_to_sell: string;
    };
  };
}

function SignalCard({ signal }: { signal: SignalData }) {
  const { explanation } = signal;
  const isInvestment = explanation.investment_focus;
  const dividend = explanation.factors?.dividend;
  const entryTiming = explanation.factors?.entry_timing;
  const guidance = explanation.investment_guidance;

  return (
    <div className="signal-card">
      <div className="signal-header">
        <span className={`signal-badge signal-${signal.signal_type.toLowerCase()}`}>
          {signal.signal_type}
        </span>
        {isInvestment && (
          <span className="investment-badge">Investment Signal</span>
        )}
        <span>Confidence: {signal.confidence_score}%</span>
      </div>

      {/* Dividend Information */}
      {dividend?.is_dividend_stock && (
        <div className="dividend-info">
          <div className="dividend-yield">
            💰 Dividend Yield: {dividend.dividend_yield}%
          </div>
          {dividend.dividend_per_share && (
            <div>Dividend per Share: ${dividend.dividend_per_share}</div>
          )}
        </div>
      )}

      {/* Entry Timing */}
      {entryTiming && (
        <div className={`entry-timing timing-${entryTiming.timing.toLowerCase()}`}>
          📈 Entry Timing: {entryTiming.timing}
        </div>
      )}

      {/* Investment Guidance */}
      {guidance && (
        <div className="investment-guidance">
          <h4>Investment Guidance</h4>
          <ul>
            <li><strong>When to Buy:</strong> {guidance.when_to_buy}</li>
            <li><strong>How Long to Hold:</strong> {guidance.how_long_to_hold}</li>
            <li><strong>When to Sell:</strong> {guidance.when_to_sell}</li>
          </ul>
        </div>
      )}

      {/* Holding Period Badge */}
      <div className="holding-period">
        ⏱️ Hold Period: {signal.holding_period}
        {signal.holding_period === "LONG" && " (5+ years)"}
      </div>
    </div>
  );
}
```

---

### 2. Stock Detail Page

#### Add Investment Guidance Section

```tsx
// StockDetailPage.tsx
function InvestmentGuidance({ signal }: { signal: SignalData }) {
  const guidance = signal.explanation?.investment_guidance;
  
  if (!guidance) return null;

  return (
    <div className="investment-guidance-section">
      <h3>Investment Guidance</h3>
      
      <div className="guidance-grid">
        <div className="guidance-card">
          <h4>When to Buy</h4>
          <div className={`timing-badge timing-${guidance.when_to_buy.toLowerCase()}`}>
            {guidance.when_to_buy}
          </div>
          <p>
            {guidance.when_to_buy === "GOOD" && "Good entry point - consider buying"}
            {guidance.when_to_buy === "FAIR" && "Fair entry point - acceptable"}
            {guidance.when_to_buy === "WAIT" && "Wait for better entry point"}
          </p>
        </div>

        <div className="guidance-card">
          <h4>How Long to Hold</h4>
          <div className="hold-period-badge">
            {guidance.how_long_to_hold}
          </div>
          <p>
            {guidance.how_long_to_hold === "LONG" && "Hold for 5+ years for best results"}
            {guidance.how_long_to_hold === "MEDIUM" && "Hold for 1-5 years"}
            {guidance.how_long_to_hold === "SHORT" && "Short-term position only"}
          </p>
        </div>

        <div className="guidance-card">
          <h4>When to Sell</h4>
          <p>{guidance.when_to_sell}</p>
        </div>
      </div>
    </div>
  );
}
```

---

### 3. Dividend Information Display

#### Add Dividend Card Component

```tsx
// DividendCard.tsx
interface DividendData {
  dividend_yield?: number;
  dividend_per_share?: number;
  dividend_payout_ratio?: number;
  is_dividend_stock?: boolean;
}

function DividendCard({ dividend }: { dividend: DividendData }) {
  if (!dividend?.is_dividend_stock) {
    return (
      <div className="dividend-card no-dividend">
        <p>This is not a dividend stock (growth-focused)</p>
      </div>
    );
  }

  const yieldColor = dividend.dividend_yield! > 5 ? "excellent" :
                     dividend.dividend_yield! > 3 ? "good" : "moderate";
  const payoutStatus = dividend.dividend_payout_ratio! > 90 ? "high-risk" :
                       dividend.dividend_payout_ratio! < 30 ? "low" : "healthy";

  return (
    <div className="dividend-card">
      <h3>💰 Dividend Information</h3>
      
      <div className="dividend-metrics">
        <div className="metric">
          <label>Dividend Yield</label>
          <div className={`value yield-${yieldColor}`}>
            {dividend.dividend_yield}%
          </div>
          {dividend.dividend_yield! > 5 && (
            <span className="badge">Excellent</span>
          )}
        </div>

        {dividend.dividend_per_share && (
          <div className="metric">
            <label>Annual Dividend per Share</label>
            <div className="value">${dividend.dividend_per_share}</div>
          </div>
        )}

        {dividend.dividend_payout_ratio && (
          <div className="metric">
            <label>Payout Ratio</label>
            <div className={`value payout-${payoutStatus}`}>
              {dividend.dividend_payout_ratio}%
            </div>
            <span className="status">
              {payoutStatus === "healthy" && "Sustainable"}
              {payoutStatus === "high-risk" && "At Risk"}
              {payoutStatus === "low" && "Room for Growth"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### 4. Signal List/Table View

#### Update Signal Table Columns

```tsx
// SignalTable.tsx
const columns = [
  { header: "Symbol", accessor: "symbol" },
  { header: "Signal", accessor: "signal_type" },
  { header: "Confidence", accessor: "confidence_score" },
  { header: "Dividend Yield", accessor: (row) => 
    row.explanation?.factors?.dividend?.dividend_yield || "N/A"
  },
  { header: "Entry Timing", accessor: (row) => 
    row.explanation?.factors?.entry_timing?.timing || "N/A"
  },
  { header: "Hold Period", accessor: "holding_period" },
  { header: "Risk", accessor: "risk_level" },
];
```

---

## 🎨 CSS/Styling Recommendations

### Entry Timing Badges

```css
.timing-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.875rem;
}

.timing-good {
  background-color: #10b981;
  color: white;
}

.timing-fair {
  background-color: #f59e0b;
  color: white;
}

.timing-wait {
  background-color: #ef4444;
  color: white;
}
```

### Dividend Yield Colors

```css
.yield-excellent {
  color: #10b981; /* Green for 5%+ */
  font-weight: 700;
}

.yield-good {
  color: #3b82f6; /* Blue for 3-5% */
}

.yield-moderate {
  color: #6b7280; /* Gray for <3% */
}
```

### Investment Guidance Cards

```css
.investment-guidance-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  color: white;
  margin: 24px 0;
}

.guidance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.guidance-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 16px;
}
```

---

## 📊 Data Flow Example

### Fetching Signal with Investment Data

```tsx
// hooks/useSignal.ts
async function fetchSignal(symbol: string) {
  const response = await fetch(`/api/v1/stocks/${symbol}/signal`);
  const data = await response.json();
  
  return {
    ...data.data,
    // Extract investment-specific data
    isInvestmentSignal: data.data.explanation?.investment_focus || false,
    dividendYield: data.data.explanation?.factors?.dividend?.dividend_yield,
    entryTiming: data.data.explanation?.factors?.entry_timing?.timing,
    investmentGuidance: data.data.explanation?.investment_guidance,
  };
}
```

---

## ✅ Checklist for Frontend Updates

### Required Updates:
- [ ] Update signal display to show "Investment Signal" badge
- [ ] Add dividend yield display in signal card
- [ ] Add entry timing indicator (GOOD/FAIR/WAIT)
- [ ] Add investment guidance section (when to buy/hold/sell)
- [ ] Update holding period display with context (e.g., "LONG (5+ years)")
- [ ] Add dividend information card to stock detail page
- [ ] Update signal table/list to show dividend yield column
- [ ] Add styling for entry timing badges
- [ ] Add styling for dividend yield colors
- [ ] Update TypeScript interfaces to include new fields

### Optional Enhancements:
- [ ] Add tooltip explaining investment vs trading signals
- [ ] Add visual indicator for dividend sustainability
- [ ] Add comparison with sector average dividend yield
- [ ] Add historical dividend growth chart
- [ ] Add "Why this is a good investment" explanation section

---

## 🔍 Example API Response

### Full Signal Response Example

```json
{
  "data": {
    "id": 123,
    "stock_id": 1,
    "signal_type": "BUY",
    "confidence_score": 78.5,
    "risk_level": "LOW",
    "holding_period": "LONG",
    "created_at": "2026-02-03T12:00:00Z",
    "explanation": {
      "summary": "BUY signal for long-term investing with 78.5% confidence",
      "investment_focus": true,
      "factors": {
        "dividend": {
          "score": 80,
          "dividend_yield": 3.5,
          "dividend_per_share": 2.50,
          "dividend_payout_ratio": 45.2,
          "is_dividend_stock": true
        },
        "fundamental": {
          "score": 85,
          "pe_ratio": 18.5,
          "earnings_growth": 12.3,
          "debt_ratio": 35.0
        },
        "long_term_trend": {
          "score": 70
        },
        "entry_timing": {
          "score": 65,
          "timing": "GOOD"
        }
      },
      "investment_guidance": {
        "when_to_buy": "GOOD",
        "how_long_to_hold": "LONG",
        "when_to_sell": "If fundamentals deteriorate or dividend is cut"
      },
      "triggers": [
        "High dividend yield (3.5%) - excellent for income",
        "Sustainable payout ratio (45.2%) - healthy balance",
        "Strong earnings growth (12.3%) - dividend may increase"
      ],
      "risks": [
        "Debt ratio: 35.0%",
        "Dividend payout: 45.2%"
      ]
    }
  },
  "meta": {
    "timestamp": "2026-02-03T12:00:00Z",
    "cache_hit": false
  }
}
```

---

## 🚀 Quick Start

1. **Update TypeScript interfaces** to include new fields
2. **Add dividend display** to signal cards
3. **Add investment guidance section** to stock detail page
4. **Update styling** for new badges and indicators
5. **Test with real API responses** to ensure all fields display correctly

---

## 📝 Notes

- All new fields are **optional** - handle `null`/`undefined` gracefully
- `investment_focus: true` indicates this is an investment signal (not trading)
- Dividend data may be `null` for growth stocks (no dividend)
- Entry timing is only for investment signals (not trading signals)
