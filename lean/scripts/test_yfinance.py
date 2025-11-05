#!/usr/bin/env python3
"""
Comprehensive YFinance diagnostic script
Run this on both host and inside Docker to compare results
"""
import sys
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print("=" * 70)
print("YFINANCE DIAGNOSTIC TEST")
print("=" * 70)
print(f"Python: {sys.version}")
print(f"YFinance version: {yf.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"Test time: {datetime.now()}")
print("=" * 70)

def test_ticker_info(symbol="AAPL"):
    """Test 1: Ticker.info (uses quoteSummary API)"""
    print(f"\n[TEST 1] Ticker.info for {symbol}")
    print("-" * 70)
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"✓ SUCCESS: Got {len(info)} fields")
        print(f"  Company: {info.get('longName', 'N/A')}")
        print(f"  Price: ${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}")
        print(f"  Market Cap: ${info.get('marketCap', 'N/A'):,}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {str(e)[:100]}")
        return False

def test_ticker_history_daily(symbol="AAPL"):
    """Test 2: Ticker.history daily data"""
    print(f"\n[TEST 2] Ticker.history daily data for {symbol}")
    print("-" * 70)
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1d")
        print(f"✓ SUCCESS: Downloaded {len(df)} daily bars")
        print(f"  Date range: {df.index[0]} to {df.index[-1]}")
        print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")
        print(f"  Columns: {list(df.columns)}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {str(e)[:100]}")
        return False

def test_ticker_history_intraday(symbol="AAPL"):
    """Test 3: Ticker.history intraday data (5min)"""
    print(f"\n[TEST 3] Ticker.history 5-minute intraday for {symbol}")
    print("-" * 70)
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="5m")
        print(f"✓ SUCCESS: Downloaded {len(df)} 5-min bars")
        if len(df) > 0:
            print(f"  Date range: {df.index[0]} to {df.index[-1]}")
            print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")
            print(f"  First 3 rows:")
            print(df.head(3))
        else:
            print(f"  ⚠️  WARNING: Empty DataFrame returned (no data)")
        return len(df) > 0
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {str(e)[:100]}")
        return False

def test_download_function(symbol="AAPL"):
    """Test 4: yf.download() function"""
    print(f"\n[TEST 4] yf.download() for {symbol}")
    print("-" * 70)
    try:
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        print(f"✓ SUCCESS: Downloaded {len(df)} bars")
        if len(df) > 0:
            print(f"  Date range: {df.index[0]} to {df.index[-1]}")
            print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")
        else:
            print(f"  ⚠️  WARNING: Empty DataFrame returned (no data)")
        return len(df) > 0
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {str(e)[:100]}")
        return False

def test_fast_info(symbol="AAPL"):
    """Test 5: Ticker.fast_info (lightweight API)"""
    print(f"\n[TEST 5] Ticker.fast_info for {symbol}")
    print("-" * 70)
    try:
        ticker = yf.Ticker(symbol)
        fast_info = ticker.fast_info
        print(f"✓ SUCCESS: Got fast_info")
        print(f"  Last price: ${fast_info.get('lastPrice', fast_info.get('last_price', 'N/A'))}")
        print(f"  Available fields: {list(fast_info.keys())[:10]}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {str(e)[:100]}")
        return False

def test_multiple_tickers():
    """Test 6: Multiple tickers"""
    print(f"\n[TEST 6] Testing multiple tickers (quick check)")
    print("-" * 70)
    symbols = ["AAPL", "MSFT", "GOOGL"]
    results = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="1d")
            success = len(df) > 0
            results[symbol] = "✓" if success else "✗ (empty)"
        except Exception as e:
            results[symbol] = f"✗ ({type(e).__name__})"

    for symbol, result in results.items():
        print(f"  {symbol}: {result}")

    return all("✓" in r for r in results.values())

def main():
    """Run all tests"""
    results = {}

    # Run tests
    results["Test 1: Ticker.info"] = test_ticker_info()
    results["Test 2: Daily history"] = test_ticker_history_daily()
    results["Test 3: Intraday history"] = test_ticker_history_intraday()
    results["Test 4: yf.download()"] = test_download_function()
    results["Test 5: fast_info"] = test_fast_info()
    results["Test 6: Multiple tickers"] = test_multiple_tickers()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")

    print("-" * 70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests PASSED! YFinance is working correctly.")
        return 0
    elif passed == 0:
        print("\n❌ All tests FAILED! YFinance is completely blocked.")
        print("\nPossible causes:")
        print("  - IP banned by Yahoo Finance")
        print("  - Network/firewall blocking requests")
        print("  - Yahoo changed their API (yfinance library needs update)")
        return 1
    else:
        print(f"\n⚠️  Partial success: {passed}/{total} tests passed")
        print("\nSome functionality works, but not all.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
