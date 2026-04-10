# Combs-Weschler S&P 500 Stock Screener

A dual-lens quantitative screening system encoding the investment philosophies of **Todd Combs** and **Ted Weschler** (Berkshire Hathaway investment managers) to identify undervalued S&P 500 companies.

## How It Works

The screener scores every S&P 500 stock (503 companies) through two independent lenses:

### 🎯 Combs Score (0–100) — "Is this a great business?"
| Sub-Score | Weight | What It Measures |
|-----------|--------|-----------------|
| Unit Economics | 25% | Gross, operating & net margins + margin consistency |
| Frictionless Ops | 25% | Revenue growth, acceleration, market position |
| Capital Allocation | 25% | ROIC, ROE, FCF yield, reinvestment efficiency |
| Moat Strength | 25% | Margin stability over time, pricing power vs peers |

### 🔍 Weschler Score (0–100) — "Is this mispriced?"
| Sub-Score | Weight | What It Measures |
|-----------|--------|-----------------|
| Variant Perception | 20% | PE gap, PE vs sector, PEG ratio |
| Complexity Discount | 20% | Low analyst coverage, high short interest, Altman Z grey zone |
| Distressed Value | 20% | 52-week drawdown, below 200d MA, FCF yield, low P/B |
| Business Quality | 20% | ROIC, earnings consistency, revenue stability |
| LT Compounding | 20% | 5yr earnings & revenue CAGR, dividend yield, book value growth |

### Combined Score
The average of both scores. Stocks scoring well on **both** lenses represent the highest conviction opportunities.

---

## Quick Start

### 1. Open the Notebook
```bash
cd ~/Desktop
jupyter notebook combs_weschler_screener.ipynb
```
Or open `combs_weschler_screener.ipynb` in VS Code.

### 2. Run All Cells
Click **Kernel → Restart & Run All** (or `Shift+Enter` through each cell).

- **First run**: ~12 minutes (fetches data for 503 tickers from Yahoo Finance)
- **Subsequent runs**: ~30 seconds (uses cached data, 24hr TTL)

### 3. Explore Results
The notebook outputs:
- Colour-coded master ranking table
- Scatter plot (Combs vs Weschler quadrants)
- Sector heatmap
- Top 10 lists for each lens
- Weekly change detection report

---

## Deep Dive Usage

After running all cells, add a new cell and use `deep_dive("TICKER")`:

```python
# Single stock analysis
deep_dive("AAPL")

# Compare multiple stocks
for ticker in ["ADBE", "NTAP", "ACN"]:
    deep_dive(ticker)

# Analyse a specific sector's top picks
healthcare = df[df['sector'] == 'Health Care'].nlargest(5, 'combined_score')
for ticker in healthcare.index:
    deep_dive(ticker)

# Find highest conviction stocks (Combs ≥60 AND Weschler ≥60)
conviction = df[(df['combs_score'] >= 60) & (df['weschler_score'] >= 60)]
conviction.sort_values('combined_score', ascending=False)

# Undervalued flags (high score + big drawdown)
flags = df[((df['combs_score'] >= 70) | (df['weschler_score'] >= 65)) & (df['drawdown_52w'] <= -0.25)]
flags.sort_values('combined_score', ascending=False)
```

### Reading the Deep Dive Output

Each deep dive shows colour-coded signals:

```
📊 OVERALL SCORES
   🟢 Combs Score:    72.0/100   ← Green = strong (>65)
   🟡 Weschler Score: 55.3/100   ← Yellow = average (40-60)
   🔴 Combined Score: 38.2/100   ← Red = weak (<45)

🎯 COMBS BREAKDOWN
   🟢 Capital Allocation: 22.4/25
     ★ ROIC:            68.3%   (wt: 35%)   ← ★ = highest-weighted metric
       ROE:             45.1%   (wt: 25%)
       FCF Yield:       7.1%    (wt: 25%)

VERDICT: ✅ HIGH CONVICTION — Quality business at attractive valuation
```

**Score thresholds:**

| Score | Combs (business quality) | Weschler (mispricing) | Combined |
|-------|--------------------------|----------------------|----------|
| 🟢 Strong | >65 | >60 | >60 |
| 🟡 Average | 45–65 | 40–60 | 50–60 |
| 🔴 Weak | <45 | <40 | <50 |

**Verdict meanings:**
- ✅ **HIGH CONVICTION** — Combined >60 + Quality >14/20
- ⚠️ **RESEARCH FURTHER** — Promising but needs deeper due diligence
- 🟡 **MONITOR** — Decent on one lens, watch for catalyst
- ❌ **VALUE TRAP RISK** — Low quality + distressed price
- ❌ **NOT COMPELLING** — Neither lens favours

---

## Weekly Automation

The screener runs automatically every **Saturday at 8:00 AM** (local time).

### What the automation does:
1. Deletes the data cache
2. Fetches fresh financials for all 503 S&P 500 stocks
3. Runs the full scoring pipeline
4. Saves a snapshot to history
5. Emails the weekly report

### Control commands:
```bash
# Run manually now
bash ~/Desktop/run_screener.sh

# Stop weekly automation
launchctl unload ~/Library/LaunchAgents/com.brendonmuur.combs-weschler-screener.plist

# Restart automation
launchctl load ~/Library/LaunchAgents/com.brendonmuur.combs-weschler-screener.plist

# Check automation status
launchctl list | grep combs

# View run logs
cat ~/Desktop/output/history/run_log.txt
```

---

## Email Alerts

Weekly emails are sent to `brendon.muur@gmail.com` every Saturday after the automated run.

### Email contents:
1. **Top 20 Roster Changes** — Stocks entering/exiting the Combs Top 20 and Weschler Top 20 separately
2. **Highest Conviction** — All stocks with Combs ≥60 AND Weschler ≥60, ordered by combined score
3. **Weekly Summary** — Top picks, score ranges, top 10 each lens, monthly big movers

Emails are sent **every week**, even if no roster changes are detected.

### Email configuration:
The email config is in the last code cell of the notebook (`EMAIL_CONFIG`):

```python
EMAIL_CONFIG = {
    'enabled': True,
    'to': 'brendon.muur@gmail.com',
    'from': 'brendon.muur@gmail.com',
    'smtp_host': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_user': 'brendon.muur@gmail.com',
    'smtp_pass': '<app-password>',  # Gmail App Password
}
```

**To change the recipient**, update `'to'` in the config.

**To generate a new Gmail App Password:**
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Sign in and enable 2-Step Verification if needed
3. Create a new app password named "Combs Weschler Screener"
4. Copy the 16-character code into `smtp_pass`

---

## File Structure

```
~/Desktop/
├── combs_weschler_screener.ipynb    # Main notebook
├── run_screener.sh                  # Weekly automation script
├── README.md                       # This file
├── .gitignore
├── data/
│   ├── sp500_cache.pkl              # Cached financial data (24hr TTL)
│   └── sp500_full_list.csv          # S&P 500 ticker list (503 companies)
└── output/
    ├── watchlist.csv                # Top 50 stocks with scores
    ├── combs_vs_weschler_scatter.png # Quadrant scatter plot
    ├── sector_heatmap.png           # Sector score heatmap
    └── history/
        ├── score_history.csv        # Cumulative history (all runs)
        ├── snapshot_YYYY-MM-DD.csv  # Individual daily snapshots
        ├── report_YYYY-MM-DD.txt    # Weekly reports
        └── run_log.txt              # Automation run log
```

---

## Refreshing Data

```bash
# Delete cache to force fresh data on next run
rm ~/Desktop/data/sp500_cache.pkl

# Update S&P 500 ticker list (if constituents change)
rm ~/Desktop/data/sp500_full_list.csv
# The notebook will re-fetch from Wikipedia on next run
```

---

## Adjusting Weights

All scoring weights are configurable in Cell 1 of the notebook:

```python
# Increase emphasis on capital allocation for Combs
COMBS_WEIGHTS = {
    'unit_economics': 0.20,
    'frictionless_ops': 0.20,
    'capital_allocation': 0.35,  # increased
    'moat_strength': 0.25,
}

# Increase emphasis on distressed value for Weschler
WESCHLER_WEIGHTS = {
    'variant_perception': 0.15,
    'complexity_discount': 0.15,
    'distressed_value': 0.30,   # increased
    'business_quality': 0.25,
    'long_term_compounding': 0.15,
}
```

> **Note:** The `COMBS_WEIGHTS` and `WESCHLER_WEIGHTS` dicts are defined for future use. Currently the weights are applied directly in the scoring formulas. To make the dicts active, update the scoring cells to reference them.

---

## Dependencies

```bash
pip install yfinance pandas numpy matplotlib seaborn scipy lxml html5lib requests
```

---

## Disclaimer

This tool identifies candidates for further research, not buy signals. Free API data has delays (typically 1 day for price, quarterly for financials). Always do your own due diligence.
