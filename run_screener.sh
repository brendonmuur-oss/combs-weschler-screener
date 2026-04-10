#!/bin/bash
# ============================================================
# Combs-Weschler Screener — Weekly Auto-Run Script
# Deletes cache, re-fetches all S&P 500 data, runs analysis,
# saves snapshot to history for week/month change tracking.
# ============================================================

NOTEBOOK_DIR="/Users/brendonmuur/Desktop"
CACHE_FILE="${NOTEBOOK_DIR}/data/sp500_cache.pkl"
NOTEBOOK="${NOTEBOOK_DIR}/combs_weschler_screener.ipynb"
LOG_FILE="${NOTEBOOK_DIR}/output/history/run_log.txt"

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
    print('SUCCESS')
except Exception as e:
    nbformat.write(nb, 'combs_weschler_screener.ipynb')
    print(f'ERROR: {e}')
" >> "$LOG_FILE" 2>&1

echo "$(date): Run complete" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
