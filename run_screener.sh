#!/bin/bash
# ============================================================
# Combs-Weschler Screener — Weekly Auto-Run Script
# Deletes cache, re-fetches all S&P 500 data, runs analysis,
# exports data for Streamlit, pushes to GitHub.
# ============================================================
set -e

NOTEBOOK_DIR="/Users/brendonmuur/Desktop"
CACHE_FILE="${NOTEBOOK_DIR}/data/sp500_cache.pkl"
NOTEBOOK="${NOTEBOOK_DIR}/combs_weschler_screener.ipynb"
LOG_FILE="${NOTEBOOK_DIR}/output/history/run_log.txt"
RESULTS_PKL="${NOTEBOOK_DIR}/data/analysis_results.pkl"
RESULTS_CSV="${NOTEBOOK_DIR}/data/screener_results.csv"

mkdir -p "${NOTEBOOK_DIR}/output/history"

echo "$(date): Starting Combs-Weschler weekly run..." >> "$LOG_FILE"

# Delete cache to force fresh data fetch
if [ -f "$CACHE_FILE" ]; then
    rm "$CACHE_FILE"
    echo "$(date): Cache deleted" >> "$LOG_FILE"
fi

# Execute notebook
cd "$NOTEBOOK_DIR"
python3 -c "
import nbformat
from nbclient import NotebookClient

nb = nbformat.read('combs_weschler_screener.ipynb', as_version=4)
for cell in nb.cells:
    if cell.cell_type == 'code':
        cell.outputs = []
        cell.execution_count = None

client = NotebookClient(nb, timeout=1800, kernel_name='python3')
try:
    client.execute()
    nbformat.write(nb, 'combs_weschler_screener.ipynb')
    print('NOTEBOOK: SUCCESS')
except Exception as e:
    nbformat.write(nb, 'combs_weschler_screener.ipynb')
    print(f'NOTEBOOK: ERROR - {e}')
" >> "$LOG_FILE" 2>&1

# Export results CSV for Streamlit
python3 -c "
import pickle, pandas as pd
with open('data/analysis_results.pkl', 'rb') as f:
    df = pickle.load(f)
export_cols = ['company','sector','market_cap','description',
    'combs_score','weschler_score','combined_score',
    'combs_unit_economics','combs_frictionless','combs_capital_allocation','combs_moat',
    'weschler_variant','weschler_complexity','weschler_distressed','weschler_quality','weschler_compounding',
    'combs_style_flag','weschler_style_flag',
    'trailing_pe','forward_pe','peg_ratio','price_to_book','price_to_sales',
    'roic','roe','fcf_yield','gross_margin','operating_margin','net_margin',
    'revenue_cagr_3y','revenue_cagr_5y','earnings_cagr_3y','earnings_cagr_5y',
    'debt_to_equity','interest_coverage','altman_z',
    'drawdown_52w','price_vs_200ma','current_price',
    'short_percent','analyst_count','dividend_yield',
    'margin_stability','margin_trend','earnings_consistency','revenue_stability',
    'book_value_growth','reinvestment_rate','pe_gap','beta']
avail = [c for c in export_cols if c in df.columns]
df[avail].to_csv('data/screener_results.csv')
print(f'CSV EXPORT: {len(df)} stocks')
" >> "$LOG_FILE" 2>&1

echo "$(date): Notebook + CSV export complete" >> "$LOG_FILE"

# Git commit and push updated data
cd "$NOTEBOOK_DIR"
git add -A
git commit -m "Weekly run: $(date +%Y-%m-%d)" --allow-empty >> "$LOG_FILE" 2>&1

# Push to GitHub (if remote is configured)
if git remote get-url origin >/dev/null 2>&1; then
    git push origin main >> "$LOG_FILE" 2>&1 || git push origin master >> "$LOG_FILE" 2>&1
    echo "$(date): Pushed to GitHub" >> "$LOG_FILE"
else
    echo "$(date): No GitHub remote configured — skipping push" >> "$LOG_FILE"
fi

echo "$(date): Run complete" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
