# Finnhub Data Download Setup

## Why Finnhub?

Yahoo Finance was rate-limiting all requests (429 errors). Finnhub offers:
- Free tier: 60 API calls/minute
- Better for intraday data (1min, 5min, 15min, 30min, 60min)
- More reliable than YFinance

## Quick Setup

### 1. Get API Key
Visit: https://finnhub.io/register
- Sign up with email (takes 30 seconds)
- Copy your API key from dashboard

### 2. Add to Environment

**Option A: Using .env file (recommended)**
```bash
cd /home/user/Stock-Prediction-Models/lean
echo "FINNHUB_API_KEY=your_actual_key_here" > .env
```

**Option B: Export in shell**
```bash
export FINNHUB_API_KEY=your_actual_key_here
```

### 3. Rebuild Docker Image
```bash
cd /home/user/Stock-Prediction-Models/lean
docker-compose build --no-cache
```

### 4. Start Pod
```bash
docker-compose down
docker-compose up -d
docker-compose exec lean-engine bash
```

### 5. Download Data (inside pod)
```bash
# Make sure key is set (check with: echo $FINNHUB_API_KEY)
export FINNHUB_API_KEY=your_key  # if not in .env

# Download default 10 tech tickers (30 days, 5min intervals)
python /Lean/scripts/download_market_data.py --source finnhub

# Download custom tickers
python /Lean/scripts/download_market_data.py --source finnhub --tickers AAPL MSFT GOOGL

# Download 1-minute data
python /Lean/scripts/download_market_data.py --source finnhub --interval 1

# Download 60 days of data
python /Lean/scripts/download_market_data.py --source finnhub --days 60
```

### 6. Verify Downloaded Data
```bash
# List all downloaded tickers
ls -lh /Lean/data/custom/

# Check AAPL data
head /Lean/data/custom/aapl/aapl_5min.csv

# Count rows
wc -l /Lean/data/custom/aapl/aapl_5min.csv
```

## Usage Examples

### Download All Default Tickers
```bash
python /Lean/scripts/download_market_data.py --source finnhub
```
Downloads: AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, AMD, INTC, NFLX

### Download Custom Watchlist
```bash
python /Lean/scripts/download_market_data.py \
  --source finnhub \
  --tickers SPY QQQ IWM TLT GLD \
  --days 60 \
  --interval 5
```

### High-Resolution Intraday Data
```bash
python /Lean/scripts/download_market_data.py \
  --source finnhub \
  --tickers AAPL \
  --interval 1 \
  --days 7
```

## Fallback to YFinance

If Finnhub is unavailable, you can still use YFinance (with rate limits):
```bash
python /Lean/scripts/download_market_data.py --source yfinance --tickers AAPL
```

## Troubleshooting

### "FINNHUB_API_KEY environment variable not set"
- Make sure you added the key to .env or exported it
- Inside pod, check: `echo $FINNHUB_API_KEY`
- Docker-compose reads .env automatically if it's in the same directory

### "No data returned for TICKER"
- Check if ticker symbol is correct (use uppercase: AAPL not aapl)
- Some tickers may not have intraday data on Finnhub
- Try a different ticker (AAPL, MSFT usually work)

### "Rate limit exceeded"
- Finnhub free tier: 60 calls/min
- Add delays between large batches
- Script already includes 1-second delays

## Data Format

Downloaded CSV files are in LEAN format (no header):
```
20241001 09:30:00,150.2500,150.5000,150.1200,150.4500,1250000
DateTime,Open,High,Low,Close,Volume
```

- DateTime: UTC timezone (converted from market time)
- Prices: 4 decimal places
- Volume: Integer

## Next Steps

After downloading data, you can:
1. Verify data with helper script: `/Lean/scripts/lean-helper.sh` (option 2, 3)
2. Run backtest: `dotnet QuantConnect.Lean.Launcher.dll --config /Lean/config/config.custom.json`
3. Check results: `/Results/` directory
