#!/bin/bash

# ==============================================================================
# Run Custom Data + Alert Strategy Backtest
# ==============================================================================
#
# This script automates the complete workflow:
# 1. Downloads YFinance data
# 2. Configures LEAN
# 3. Runs backtest with custom data and alert execution
#
# Usage:
#   ./scripts/run_custom_backtest.sh
#   ./scripts/run_custom_backtest.sh --skip-download
#
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
TICKERS="AAPL MSFT GOOGL AMZN NVDA TSLA META AMD INTC NFLX"
PERIOD="1mo"
INTERVAL="5m"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Custom LEAN Backtest Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we should skip download
SKIP_DOWNLOAD=false
if [ "$1" == "--skip-download" ]; then
    SKIP_DOWNLOAD=true
fi

# Step 1: Download data (unless skipped)
if [ "$SKIP_DOWNLOAD" == "false" ]; then
    echo -e "${GREEN}Step 1/4: Downloading market data${NC}"
    echo "Tickers: $TICKERS"
    echo "Period: $PERIOD"
    echo "Interval: $INTERVAL"
    echo ""

    python scripts/download_yfinance_data.py \
        --tickers $TICKERS \
        --period $PERIOD \
        --interval $INTERVAL \
        --data-dir ./data/custom

    echo ""
else
    echo -e "${YELLOW}Step 1/4: Skipping data download${NC}"
    echo ""
fi

# Step 2: Verify data
echo -e "${GREEN}Step 2/4: Verifying data files${NC}"

data_count=$(find data/custom -name "*_5min.csv" 2>/dev/null | wc -l || echo "0")
echo "Found $data_count data files"

if [ "$data_count" -eq "0" ]; then
    echo -e "${YELLOW}⚠️  Warning: No data files found!${NC}"
    echo "   Run without --skip-download to download data"
    exit 1
fi

echo ""

# Step 3: Configure LEAN
echo -e "${GREEN}Step 3/4: Configuring LEAN${NC}"

# Check if custom config exists
if [ ! -f "config/config.custom.json" ]; then
    echo -e "${YELLOW}⚠️  config.custom.json not found${NC}"
    exit 1
fi

# Copy custom config to main config
cp config/config.custom.json config/config.json
echo "✓ Using config.custom.json"
echo ""

# Step 4: Run backtest
echo -e "${GREEN}Step 4/4: Running backtest${NC}"
echo ""

docker-compose run --rm \
    -v "$(pwd)/data:/Lean/data" \
    -v "$(pwd)/algorithms:/Lean/Algorithm" \
    -v "$(pwd)/custom:/Lean/Algorithm/custom" \
    -v "$(pwd)/config:/Lean/Launcher" \
    -v "$(pwd)/results:/Results" \
    lean-engine

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Backtest complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Results saved to: ./results/"
echo "View logs: docker-compose logs"
echo ""
