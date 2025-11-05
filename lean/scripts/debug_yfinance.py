#!/usr/bin/env python3
"""
Debug script to see exactly what Yahoo Finance is returning
"""
import yfinance as yf
import requests

print("=" * 60)
print("Testing YFinance with detailed output")
print("=" * 60)

# Test 1: Direct API call to see raw response
print("\n1. Testing raw Yahoo Finance API response:")
ticker = "AAPL"
url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
params = {"modules": "price"}
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"   Response Length: {len(response.text)} chars")
    print(f"   First 500 chars of response:")
    print(f"   {response.text[:500]}")
    print()
except Exception as e:
    print(f"   ✗ Request failed: {e}\n")

# Test 2: YFinance Ticker.info (what the test script uses)
print("2. Testing yf.Ticker().info:")
try:
    stock = yf.Ticker("AAPL")
    info = stock.info
    print(f"   ✓ Success! Got {len(info)} fields")
    print(f"   Name: {info.get('longName', 'N/A')}")
    print(f"   Price: ${info.get('currentPrice', 'N/A')}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    print(f"   Error type: {type(e).__name__}")

# Test 3: YFinance download (what we actually need for market data)
print("\n3. Testing yf.download() for historical data:")
try:
    data = yf.download("AAPL", period="5d", interval="5m", progress=False)
    print(f"   ✓ Success! Downloaded {len(data)} rows")
    print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    print(f"   First row:")
    print(f"   {data.head(1)}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    print(f"   Error type: {type(e).__name__}")

# Test 4: Check if it's a ticker-specific issue
print("\n4. Testing multiple tickers:")
for ticker in ["AAPL", "MSFT", "GOOGL", "INVALID"]:
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        print(f"   {ticker}: ✓ {len(data)} rows")
    except Exception as e:
        print(f"   {ticker}: ✗ {type(e).__name__}: {str(e)[:60]}")

print("\n" + "=" * 60)
print("Diagnosis complete")
print("=" * 60)
