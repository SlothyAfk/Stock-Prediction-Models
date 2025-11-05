# YFinance Docker Workaround

## The Problem

Yahoo Finance blocks requests from Docker containers while allowing requests from host systems. This is due to environment fingerprinting (SSL/TLS signatures, Python version, network stack, etc.).

**Symptom:**
- ✅ YFinance works on your host system
- ❌ YFinance fails inside Docker pod with 429 errors and "Invalid Crumb"

## The Solution

Download data on your **host system** (where yfinance works), save it to `lean/data/custom/`, which is automatically mounted into the Docker pod at `/Lean/data/custom/`.

The pod can then read this pre-downloaded data for backtesting without hitting Yahoo's blocks.

## Usage

### Step 1: Download Data on Host

```bash
# Exit the Docker pod if you're in it
exit

# Navigate to the lean directory
cd ~/Stock-Prediction-Models/lean

# Install required packages on host (if not already installed)
pip3 install yfinance pandas pytz

# Download default 10 tech stocks (1 month, 5min intervals)
python3 download_data_host.py

# Or download custom tickers
python3 download_data_host.py --tickers AAPL MSFT GOOGL --period 3mo --interval 5m

# Or download daily data
python3 download_data_host.py --interval 1d --period 1y
```

### Step 2: Verify Data in Docker Pod

```bash
# Enter the pod
docker-compose exec lean-engine bash

# List downloaded tickers
ls -lh /Lean/data/custom/

# Check AAPL data (should see CSV in LEAN format)
head /Lean/data/custom/aapl/aapl_5min.csv

# Count rows
wc -l /Lean/data/custom/aapl/aapl_5min.csv
```

Expected format (no header):
```
20241001 09:30:00,150.2500,150.5000,150.1200,150.4500,1250000
20241001 09:35:00,150.4500,150.6000,150.3000,150.5500,980000
```

### Step 3: Run Backtest

```bash
# Inside the pod
cd /Lean/Launcher/bin/Debug

# Run backtest with custom data
dotnet QuantConnect.Lean.Launcher.dll --config /Lean/config/config.custom.json

# Check results
ls -lh /Results/
```

## Options

### Download Different Time Periods

```bash
# 1 day of 1-minute data
python3 download_data_host.py --period 1d --interval 1m

# 3 months of 5-minute data
python3 download_data_host.py --period 3mo --interval 5m

# 1 year of 15-minute data
python3 download_data_host.py --period 1y --interval 15m

# 1 year of daily data
python3 download_data_host.py --period 1y --interval 1d
```

### Download Custom Ticker List

```bash
# Just FAANG stocks
python3 download_data_host.py --tickers AAPL META AMZN NFLX GOOGL

# ETFs
python3 download_data_host.py --tickers SPY QQQ IWM TLT GLD

# Individual stock
python3 download_data_host.py --tickers TSLA
```

## Data Format

The script automatically converts yfinance data to LEAN's expected CSV format:

**LEAN Format:**
- No header row
- Columns: DateTime,Open,High,Low,Close,Volume
- DateTime: `YYYYMMDD HH:MM:SS` in UTC (no timezone)
- Prices: 4 decimal places
- Volume: Integer

**File Structure:**
```
lean/data/custom/
├── aapl/
│   └── aapl_5min.csv
├── msft/
│   └── msft_5min.csv
└── googl/
    └── googl_5min.csv
```

## Limitations

**YFinance Intraday Data Limits:**
- **1m interval:** Max 7 days
- **2m interval:** Max 60 days
- **5m interval:** Max 60 days
- **15m interval:** Max 60 days
- **30m interval:** Max 60 days
- **1h interval:** Max 730 days (2 years)
- **1d interval:** Unlimited history

If you need more historical intraday data, consider upgrading to **IEX Cloud Starter ($9/month)** or **Alpha Vantage**.

## Troubleshooting

### "ERROR: Please run this script from the lean/ directory"
```bash
cd ~/Stock-Prediction-Models/lean
python3 download_data_host.py
```

### "ModuleNotFoundError: No module named 'yfinance'"
```bash
pip3 install yfinance pandas pytz
```

### "No data returned for TICKER"
- Check if ticker symbol is correct (use uppercase: AAPL not aapl)
- Try a different period (some tickers don't have recent intraday data)
- Check if ticker is still trading

### Data shows up on host but not in pod
```bash
# Restart the pod to refresh volume mounts
docker-compose restart lean-engine
```

## Next Steps

Once you have data downloaded:

1. ✅ Verify data format in pod
2. ✅ Run example backtest: `/Lean/algorithms/custom_data_alert_strategy.py`
3. ✅ Check results in `/Results/`
4. ✅ Create your own strategies

## Future: Upgrade to IEX Cloud

When ready for production-grade data:

- **IEX Cloud Starter:** $9/month
- Unlimited historical intraday data
- 500k API calls/month
- No Docker blocking issues
- More reliable than YFinance

See: https://iexcloud.io/pricing/
