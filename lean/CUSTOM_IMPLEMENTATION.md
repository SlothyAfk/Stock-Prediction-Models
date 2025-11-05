# Custom LEAN Implementation Guide

Complete implementation of custom data providers, execution models, and universe selection for LEAN.

## 📋 Table of Contents

- [Overview](#overview)
- [Requirements Implemented](#requirements-implemented)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Step-by-Step Guide](#step-by-step-guide)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## 🎯 Overview

This implementation demonstrates how to extend LEAN with:

1. **Custom Data Provider** - YFinance for free market data
2. **Universe Selection** - Watchlist-based stock universe
3. **Custom Backtesting** - Using downloaded local data
4. **Alert Execution** - API alerts instead of real trades

### What's Included

```
lean/
├── custom/
│   ├── data_providers/
│   │   └── yfinance_data.py          # Custom data class for YFinance
│   ├── execution_models/
│   │   └── alert_execution_model.py  # Alert-based execution
│   └── universe/
│       └── (your custom universe models)
├── algorithms/
│   └── custom_data_alert_strategy.py # Complete example algorithm
├── scripts/
│   └── download_yfinance_data.py     # Data downloader
└── config/
    └── config.custom.json            # Configuration
```

---

## ✅ Requirements Implemented

### 1. Custom Data Provider (YFinance)

**Status**: ✅ Complete

- Uses `yfinance` library to download free market data
- Downloads 5-minute intraday bars
- Converts to LEAN-compatible CSV format
- Handles timezone conversions (ET → UTC)
- Reads data via custom `PythonData` class

**Files**:
- `scripts/download_yfinance_data.py` - Downloader
- `custom/data_providers/yfinance_data.py` - LEAN data class

### 2. Universe Selection (Watchlist)

**Status**: ✅ Complete

- Defines universe of 10 tech stocks
- Easy to customize ticker list
- Automatic subscription management
- Per-symbol indicator tracking

**Implementation**: In `custom_data_alert_strategy.py` via `universe_tickers` list

### 3. Backtesting on Local Data

**Status**: ✅ Complete

- Downloads data to local filesystem
- LEAN reads from `/Lean/data/custom/` directory
- No external API calls during backtest
- Full historical replay capability

**Data Format**: CSV files in LEAN-compatible format

### 4. Custom Execution Model (API Alerts)

**Status**: ✅ Complete

- Intercepts portfolio targets before order placement
- Sends HTTP POST requests to your API
- Includes dry-run mode for testing
- Full trade signal payload (symbol, action, quantity, price)

**Files**: `custom/execution_models/alert_execution_model.py`

---

## 🚀 Quick Start

### Step 1: Download Market Data

```bash
cd lean

# Download data for default 10 tech stocks (last month, 5-min intervals)
python scripts/download_yfinance_data.py

# Or customize
python scripts/download_yfinance_data.py \
  --tickers AAPL MSFT GOOGL AMZN NVDA \
  --period 2mo \
  --interval 5m \
  --data-dir ./data/custom
```

Expected output:
```
Downloading 10 tickers
Period: 1mo, Interval: 5m
============================================================

[1/10] AAPL
  ✓ Downloaded 1956 bars
  ✓ Formatted 1956 bars for LEAN
  Date range: 20241001 09:30:00 to 20241031 16:00:00 UTC
  ✓ Saved to data/custom/aapl/aapl_5min.csv (89.2 KB)

...

✓ Successfully downloaded: 10/10 tickers
✓ Data saved to: /path/to/lean/data/custom
```

### Step 2: Build Docker Image

```bash
# Rebuild with yfinance dependency
docker-compose build --no-cache
```

### Step 3: Run Backtest

```bash
# Copy custom config
cp config/config.custom.json config/config.json

# Run backtest
docker-compose run --rm -v $(pwd)/data:/Lean/data lean-engine
```

---

## 🏗️ Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Data Download (one-time)                            │
│    yfinance → CSV files in data/custom/                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. LEAN Backtest Start                                 │
│    Algorithm calls AddData(YFinanceData, "AAPL")       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Data Reading                                         │
│    YFinanceData.GetSource() → /Lean/data/custom/aapl/  │
│    YFinanceData.Reader() → Parse CSV lines              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Algorithm Processing                                 │
│    OnData() receives price bars                         │
│    Generates trading signals                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Execution                                            │
│    SetHoldings() / Liquidate() called                   │
│    AlertExecutionModel intercepts                       │
│    HTTP POST to your API (or logs if dry-run)          │
└─────────────────────────────────────────────────────────┘
```

### Component Relationships

```
CustomDataAlertStrategy (Algorithm)
    │
    ├─→ YFinanceData (Data Provider)
    │       └─→ Reads: /Lean/data/custom/{ticker}/{ticker}_5min.csv
    │
    ├─→ AlertExecutionModel (Execution)
    │       └─→ POST to: your-api.com/trading/alerts
    │
    └─→ Universe Selection
            └─→ Static list: [AAPL, MSFT, GOOGL, ...]
```

---

## 📖 Step-by-Step Guide

### A. Setting Up Your Custom Data Provider

#### 1. Download Data

```bash
python scripts/download_yfinance_data.py --tickers AAPL MSFT --period 1mo
```

#### 2. Verify Data Files

```bash
ls -lh data/custom/aapl/
# Should show: aapl_5min.csv

head -5 data/custom/aapl/aapl_5min.csv
# Should show: DateTime,Open,High,Low,Close,Volume (no header, just data)
# 20241001 09:30:00,227.03,227.50,226.85,227.25,5428900
```

#### 3. Use in Algorithm

```python
from custom.data_providers.yfinance_data import YFinanceData

class MyAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Add custom data
        self.aapl = self.AddData(YFinanceData, "AAPL").Symbol

    def OnData(self, data: Slice):
        if self.aapl in data:
            bar = data[self.aapl]
            self.Debug(f"AAPL: ${bar.Close}")
```

### B. Setting Up Universe Selection

#### Option 1: Manual List (Simple)

```python
def Initialize(self):
    # Define your watchlist
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

    # Add each ticker
    self.symbols = {}
    for ticker in tickers:
        symbol = self.AddData(YFinanceData, ticker).Symbol
        self.symbols[ticker] = symbol
```

#### Option 2: Manual Universe Model (Framework)

```python
from AlgorithmImports import *

def Initialize(self):
    # Create symbol objects
    symbols = [
        Symbol.Create("AAPL", SecurityType.Base, Market.USA),
        Symbol.Create("MSFT", SecurityType.Base, Market.USA),
        # ...
    ]

    # Set universe
    self.SetUniverseSelection(ManualUniverseSelectionModel(symbols))
```

### C. Setting Up Alert Execution

#### 1. Dry Run (Log Only)

```python
from custom.execution_models.alert_execution_model import AlertExecutionModel

def Initialize(self):
    # Just log alerts, don't send HTTP requests
    self.SetExecution(AlertExecutionModel(dry_run=True))
```

Output:
```
🔔 ALERT: BUY 100 AAPL @ $227.50 ($22,750.00)
   [DRY RUN] Would send to: http://localhost:8000/trading/alerts
   Payload: { "symbol": "AAPL", "action": "BUY", ... }
```

#### 2. Live API Integration

```python
def Initialize(self):
    # Send real HTTP requests
    self.SetExecution(AlertExecutionModel(
        api_url="https://your-api.com/trading/alerts",
        api_key=os.environ.get("TRADING_API_KEY"),
        dry_run=False
    ))
```

#### 3. Webhook Testing

Use [webhook.site](https://webhook.site) for testing:

```python
def Initialize(self):
    self.SetExecution(AlertExecutionModel(
        api_url="https://webhook.site/your-unique-url",
        dry_run=False
    ))
```

### D. Running the Complete Example

```bash
# 1. Download data
python scripts/download_yfinance_data.py

# 2. Set algorithm in config
# Edit config/config.json:
#   "algorithm-location": "/Lean/Algorithm/custom_data_alert_strategy.py"

# 3. Run
docker-compose up
```

---

## 📚 API Reference

### YFinanceData Class

```python
class YFinanceData(PythonData):
    """Custom data class for YFinance CSV files"""

    def GetSource(self, config, date, isLiveMode):
        """Returns path to CSV file"""
        # Returns: /Lean/data/custom/{symbol}/{symbol}_5min.csv

    def Reader(self, config, line, date, isLiveMode):
        """Parses one line from CSV"""
        # Parses: DateTime,Open,High,Low,Close,Volume
        # Returns: YFinanceData object
```

**Properties**:
- `Symbol` - Symbol object
- `Time` - Bar start time (datetime)
- `EndTime` - Bar end time (datetime)
- `Open`, `High`, `Low`, `Close` - OHLC prices (float)
- `Volume` - Trading volume (int)
- `Value` - Current value (= Close)

### AlertExecutionModel Class

```python
class AlertExecutionModel(ExecutionModel):
    """Sends alerts instead of placing orders"""

    def __init__(self, api_url=None, api_key=None, dry_run=True):
        """
        Args:
            api_url: Your API endpoint
            api_key: API authentication key
            dry_run: If True, only logs (no HTTP)
        """

    def Execute(self, algorithm, targets):
        """
        Called when portfolio targets change

        Args:
            targets: List of PortfolioTarget objects

        Returns:
            Empty list (no real orders)
        """
```

**Alert Payload Format**:
```json
{
    "timestamp": "2024-10-15T10:30:00",
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 100,
    "target_quantity": 100,
    "current_quantity": 0,
    "current_price": 227.50,
    "estimated_value": 22750.00,
    "algorithm": "CustomDataAlertStrategy",
    "metadata": {
        "time_utc": "2024-10-15T14:30:00",
        "portfolio_value": 100000.00,
        "cash": 77250.00
    }
}
```

---

## 🔧 Troubleshooting

### Issue: "No data returned for AAPL"

**Cause**: YFinance API rate limiting or ticker doesn't exist

**Solution**:
```bash
# Test yfinance directly
python -c "import yfinance as yf; print(yf.Ticker('AAPL').history(period='1d'))"

# Try with longer delay between tickers
# Edit download script and add time.sleep(1) between downloads
```

### Issue: "File not found: /Lean/data/custom/aapl/aapl_5min.csv"

**Cause**: Data not mounted into Docker container

**Solution**:
```bash
# Verify volume mount in docker-compose.yml
volumes:
  - ./data:/Lean/data

# Check file exists on host
ls -la data/custom/aapl/

# Rebuild and remount
docker-compose down -v
docker-compose up
```

### Issue: "Module 'custom' not found"

**Cause**: Python path not set correctly

**Solution**:
```python
# Add at top of algorithm
import sys
sys.path.append('/Lean/Algorithm')

from custom.data_providers.yfinance_data import YFinanceData
```

### Issue: Alert HTTP request fails

**Cause**: Network connectivity or API endpoint down

**Solution**:
```python
# Use dry-run mode first
self.SetExecution(AlertExecutionModel(dry_run=True))

# Test API endpoint separately
import requests
response = requests.post("https://your-api.com/alerts", json={"test": "data"})
print(response.status_code)
```

### Issue: Timezone mismatches

**Cause**: Data timezone doesn't match algorithm timezone

**Solution**:
```python
# In algorithm Initialize()
self.SetTimeZone("America/New_York")  # Must match data timezone

# In data downloader, verify UTC conversion
lean_df['Datetime'] = lean_df['Datetime'].dt.tz_convert('UTC')
```

---

## 🎓 Advanced Usage

### Custom Indicators on YFinance Data

```python
def Initialize(self):
    symbol = self.AddData(YFinanceData, "AAPL").Symbol

    # Create indicators
    self.ema_fast = self.EMA(symbol, 20, Resolution.Minute)
    self.ema_slow = self.EMA(symbol, 50, Resolution.Minute)
    self.rsi = self.RSI(symbol, 14, Resolution.Minute)

def OnData(self, data):
    if self.ema_fast.IsReady and self.ema_slow.IsReady:
        # Use indicators
        if self.ema_fast.Current.Value > self.ema_slow.Current.Value:
            # Bullish crossover
            self.SetHoldings(symbol, 1.0)
```

### Dynamic Universe (Add/Remove Tickers)

```python
def Initialize(self):
    self.universe = {}
    self.Schedule.On(
        self.DateRules.MonthStart(),
        self.TimeRules.AfterMarketOpen("AAPL", 1),
        self.RebalanceUniverse
    )

def RebalanceUniverse(self):
    # Determine new universe (e.g., from screener API)
    new_tickers = self.GetTopMomentumStocks()

    # Remove old
    for ticker in list(self.universe.keys()):
        if ticker not in new_tickers:
            self.RemoveSecurity(self.universe[ticker])
            del self.universe[ticker]

    # Add new
    for ticker in new_tickers:
        if ticker not in self.universe:
            symbol = self.AddData(YFinanceData, ticker).Symbol
            self.universe[ticker] = symbol
```

### Multi-API Alert Dispatching

```python
class MultiAPIExecutionModel(AlertExecutionModel):
    def __init__(self):
        super().__init__(dry_run=True)
        self.apis = [
            "https://api1.com/alerts",
            "https://api2.com/alerts",
            "https://webhook.site/abc123"
        ]

    def _dispatch_alert(self, algorithm, alert):
        for api_url in self.apis:
            try:
                requests.post(api_url, json=alert, timeout=5)
            except:
                algorithm.Error(f"Failed to send to {api_url}")
```

### SQLite Data Provider (Advanced)

If you want to read from SQLite instead of CSV:

```python
import sqlite3

class SQLiteData(PythonData):
    def GetSource(self, config, date, isLiveMode):
        # Return database path
        return SubscriptionDataSource(
            "/Lean/data/market_data.db",
            SubscriptionTransportMedium.LocalFile
        )

    def Reader(self, config, line, date, isLiveMode):
        # Query database instead of parsing line
        # (More complex, requires connection management)
        pass
```

---

## 📞 Support

- **Custom Implementation Issues**: Check this guide or algorithm comments
- **LEAN Core Issues**: [QuantConnect Forum](https://www.quantconnect.com/forum)
- **YFinance Issues**: [yfinance GitHub](https://github.com/ranaroussi/yfinance)

---

## ✅ Checklist

Before running in production:

- [ ] Downloaded all required market data
- [ ] Verified data files exist and are readable
- [ ] Tested algorithm in dry-run mode
- [ ] Configured API endpoints and credentials
- [ ] Set appropriate timezone in algorithm
- [ ] Tested with small date ranges first
- [ ] Implemented proper error handling
- [ ] Set up monitoring/alerting
- [ ] Documented your custom modifications

---

<p align="center">
  <strong>Happy Custom Trading! 🚀📈</strong>
</p>
