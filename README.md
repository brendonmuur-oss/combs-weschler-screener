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

## Score Interpretation Guide

### Combs Score (0–100) — "Is this a great business?"

| Sub-Score | Max | 🟢 Strong | 🟡 Average | 🔴 Weak | Key Metrics (★ = highest weight) |
|-----------|-----|-----------|------------|---------|----------------------------------|
| Unit Economics | /25 | >18 | 12–18 | <12 | ★ Gross Margin (30%), ★ Op Margin (30%), Net Margin (20%), Margin Stability (20%) |
| Frictionless Ops | /25 | >18 | 12–18 | <12 | ★ Rev CAGR 3y (40%), Rev Acceleration (30%), Sector Position (30%) |
| Capital Allocation | /25 | >18 | 12–18 | <12 | ★ ROIC (35%), ROE (25%), FCF Yield (25%), Reinvest Rate (15%) |
| Moat Strength | /25 | >18 | 12–18 | <12 | ★ Margin Stability (35%), ★ Competitive Position (35%), Margin Trend (30%) |
| **TOTAL** | **/100** | **>65** | **45–65** | **<45** | |

### Weschler Score (0–100) — "Is this mispriced?"

| Sub-Score | Max | 🟢 Strong | 🟡 Average | 🔴 Weak | Key Metrics (★ = highest weight) |
|-----------|-----|-----------|------------|---------|----------------------------------|
| Variant Perception | /20 | >14 | 8–14 | <8 | ★ PE Gap (35%), ★ PE vs Sector (35%), PEG Ratio (30%) |
| Complexity Discount | /20 | >14 | 8–14 | <8 | ★ Analyst Coverage (30%), P/B Discount (25%), Short Interest (25%), Altman Z (20%) |
| Distressed Value | /20 | >14 | 8–14 | <8 | ★ 52w Drawdown (30%), vs 200d MA (25%), FCF Yield (25%), P/B (20%) |
| Business Quality | /20 | >14 | 8–14 | <8 | ★ ROIC (30%), Earn Consistency (25%), Rev Stability (25%), Interest Coverage (20%) |
| LT Compounding | /20 | >14 | 8–14 | <8 | ★ Earn CAGR 5y (30%), ★ Rev CAGR 5y (30%), Book Val Growth (25%), Div Yield (15%) |
| **TOTAL** | **/100** | **>60** | **40–60** | **<40** | |

### Combined Score & Verdicts

| Combined Score | Signal | Meaning |
|---------------|--------|---------|
| >60 | 🟢 Strong conviction | Quality business + attractive valuation |
| 50–60 | 🟡 Worth researching | Strong on one lens, decent on the other |
| <50 | 🔴 Neither favours | Not compelling from either angle |

| Verdict | Criteria |
|---------|----------|
| ✅ **HIGH CONVICTION** | Combined >60 AND Business Quality >14/20 |
| ⚠️ **RESEARCH FURTHER** | Combined >55 OR (Combs >65 AND Quality >12) |
| 🟡 **MONITOR** | Combined >50 AND Quality >10 |
| ❌ **VALUE TRAP RISK** | Quality <10 AND Weschler > Combs |
| ❌ **NOT COMPELLING** | None of the above |

### Quick Rules of Thumb
- **Combs >70** = Exceptional business (top ~10% of S&P 500)
- **Weschler >65** = Significant mispricing signal
- **Business Quality >15/20** = Good business underneath the distress
- **Quality <10 + big drawdown** = Likely a value trap, not an opportunity
- **Both Combs ≥60 AND Weschler ≥60** = Highest conviction (typically only 5-15 stocks)

---

## Streamlit Dashboard (Mobile Access)

The screener includes a Streamlit web dashboard for interactive analysis from any device.

### Deploy to Streamlit Community Cloud (free, permanent URL):

1. Push this repo to GitHub:
   ```bash
   # Create a GitHub repo at github.com/new, then:
   git remote add origin https://github.com/YOUR_USERNAME/combs-weschler-screener.git
   git branch -M main
   git push -u origin main
   ```

2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" → select your repo → set main file to `streamlit_app.py`
4. Deploy — you'll get a URL like `https://cw-screener.streamlit.app`

### Run locally:
```bash
pip install streamlit plotly
cd ~/Desktop
streamlit run streamlit_app.py
```

### Dashboard features:
- **Rankings tab**: Sortable table with colour-coded scores, sector filtering
- **Deep Dive tab**: Interactive single-stock analysis with all sub-scores and verdicts
- **Scatter Plot tab**: Interactive Combs vs Weschler quadrant chart (hover for details)
- **Conviction tab**: All stocks where both Combs ≥60 AND Weschler ≥60
- **Sector Heatmap tab**: Interactive heatmaps of scores by sector
- **Cheat Sheet sidebar**: Always-visible score interpretation guide

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
