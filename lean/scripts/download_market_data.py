#!/usr/bin/env python3
"""
Multi-Source Data Downloader for LEAN

Downloads historical intraday data from multiple sources and converts it to
LEAN-compatible CSV format for backtesting.

Supported Sources:
- Finnhub (recommended): Free tier with 60 calls/min
- YFinance (backup): Free but rate-limited

Features:
- Downloads 1-minute or 5-minute interval data
- Handles timezone conversions (market time to UTC)
- Saves in LEAN's expected CSV format
- Supports batch downloads for multiple tickers
- Includes data validation and error handling

Usage:
    python download_market_data.py --source finnhub
    python download_market_data.py --source yfinance --tickers AAPL MSFT
    python download_market_data.py --source finnhub --interval 1
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import time

import pandas as pd
import pytz


class DataDownloader:
    """Base class for market data downloaders"""

    def __init__(self, data_dir: str = "./data/custom"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.market_tz = pytz.timezone('America/New_York')
        self.utc_tz = pytz.UTC

    def format_for_lean(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Convert DataFrame to LEAN CSV format"""
        lean_df = df.copy()
        lean_df = lean_df.reset_index()

        # Ensure datetime column exists
        if 'Datetime' not in lean_df.columns and 'datetime' in lean_df.columns:
            lean_df.rename(columns={'datetime': 'Datetime'}, inplace=True)
        elif 'Datetime' not in lean_df.columns and lean_df.index.name == 'Datetime':
            lean_df = lean_df.reset_index()

        # Convert timezone
        if lean_df['Datetime'].dt.tz is not None:
            lean_df['Datetime'] = lean_df['Datetime'].dt.tz_convert('UTC')
        else:
            lean_df['Datetime'] = lean_df['Datetime'].dt.tz_localize(self.market_tz)
            lean_df['Datetime'] = lean_df['Datetime'].dt.tz_convert('UTC')

        lean_df['Datetime'] = lean_df['Datetime'].dt.tz_localize(None)
        lean_df['DateTime'] = lean_df['Datetime'].dt.strftime('%Y%m%d %H:%M:%S')

        # Select columns
        lean_df = lean_df[['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Round and clean
        price_cols = ['Open', 'High', 'Low', 'Close']
        lean_df[price_cols] = lean_df[price_cols].round(4)
        lean_df['Volume'] = lean_df['Volume'].astype(int)
        lean_df = lean_df.dropna()

        print(f"  ✓ Formatted {len(lean_df)} bars for LEAN")
        print(f"  Date range: {lean_df['DateTime'].iloc[0]} to {lean_df['DateTime'].iloc[-1]} UTC")

        return lean_df

    def save_csv(self, df: pd.DataFrame, ticker: str, interval: str) -> Path:
        """Save formatted data to CSV file"""
        ticker_dir = self.data_dir / ticker.lower()
        ticker_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{ticker.lower()}_{interval}min.csv"
        filepath = ticker_dir / filename

        df.to_csv(filepath, index=False, header=False)

        file_size = filepath.stat().st_size / 1024
        print(f"  ✓ Saved to {filepath} ({file_size:.1f} KB)")

        return filepath


class FinnhubDownloader(DataDownloader):
    """Finnhub data downloader (recommended - better rate limits)"""

    def __init__(self, api_key: str, data_dir: str = "./data/custom"):
        super().__init__(data_dir)

        if not api_key:
            raise ValueError("FINNHUB_API_KEY environment variable not set!")

        import finnhub
        self.client = finnhub.Client(api_key=api_key)
        print(f"✓ Finnhub client initialized")

    def download_ticker(self, ticker: str, days: int = 30, interval: int = 5) -> Optional[pd.DataFrame]:
        """Download data from Finnhub"""
        print(f"Downloading {ticker} data ({days} days, {interval}min intervals)...")

        try:
            # Finnhub uses UNIX timestamps
            end_time = int(datetime.now().timestamp())
            start_time = int((datetime.now() - timedelta(days=days)).timestamp())

            # Resolution: 1, 5, 15, 30, 60, D, W, M
            resolution = str(interval)

            # Download stock candles
            data = self.client.stock_candles(ticker, resolution, start_time, end_time)

            if data['s'] != 'ok':
                print(f"  ⚠️  No data returned for {ticker}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame({
                'Datetime': pd.to_datetime(data['t'], unit='s'),
                'Open': data['o'],
                'High': data['h'],
                'Low': data['l'],
                'Close': data['c'],
                'Volume': data['v']
            })

            # Localize to market timezone
            df['Datetime'] = df['Datetime'].dt.tz_localize('UTC').dt.tz_convert(self.market_tz)

            print(f"  ✓ Downloaded {len(df)} bars")
            return df

        except Exception as e:
            print(f"  ✗ Error downloading {ticker}: {e}")
            return None


class YFinanceDownloader(DataDownloader):
    """YFinance data downloader (backup - rate limited)"""

    def __init__(self, data_dir: str = "./data/custom"):
        super().__init__(data_dir)
        import yfinance as yf
        import requests

        # Configure session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print(f"✓ YFinance downloader initialized")

    def download_ticker(self, ticker: str, days: int = 30, interval: int = 5) -> Optional[pd.DataFrame]:
        """Download data from YFinance"""
        import yfinance as yf

        print(f"Downloading {ticker} data ({days} days, {interval}min intervals)...")

        # Add delay to avoid rate limiting
        time.sleep(2)

        try:
            ticker_obj = yf.Ticker(ticker, session=self.session)

            # YFinance interval format
            interval_str = f"{interval}m"
            period_str = f"{days}d"

            df = ticker_obj.history(period=period_str, interval=interval_str)

            if df.empty:
                print(f"  ⚠️  No data returned for {ticker}")
                return None

            # Rename columns to match our format
            df = df.reset_index()
            df.rename(columns={'Datetime': 'Datetime', 'Date': 'Datetime'}, inplace=True)

            print(f"  ✓ Downloaded {len(df)} bars")
            return df

        except Exception as e:
            print(f"  ✗ Error downloading {ticker}: {e}")
            return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download market data from multiple sources for LEAN backtesting"
    )

    parser.add_argument(
        "--source",
        choices=["finnhub", "yfinance"],
        default="finnhub",
        help="Data source to use (default: finnhub)"
    )

    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "INTC", "NFLX"],
        help="List of ticker symbols to download (default: 10 tech stocks)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days of historical data (default: 30)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        choices=[1, 5, 15, 30, 60],
        default=5,
        help="Data interval in minutes (default: 5)"
    )

    parser.add_argument(
        "--data-dir",
        default="./data/custom",
        help="Directory to save downloaded data (default: ./data/custom)"
    )

    parser.add_argument(
        "--api-key",
        help="API key (defaults to FINNHUB_API_KEY env var for Finnhub)"
    )

    args = parser.parse_args()

    # Create downloader
    try:
        if args.source == "finnhub":
            api_key = args.api_key or os.environ.get('FINNHUB_API_KEY')
            downloader = FinnhubDownloader(api_key=api_key, data_dir=args.data_dir)
        else:
            downloader = YFinanceDownloader(data_dir=args.data_dir)
    except ValueError as e:
        print(f"❌ Error: {e}")
        print(f"")
        print(f"To use Finnhub:")
        print(f"  1. Get free API key at: https://finnhub.io/register")
        print(f"  2. Set environment variable: export FINNHUB_API_KEY=your_key")
        print(f"  3. Or pass --api-key your_key")
        print(f"")
        print(f"Or use: --source yfinance (rate-limited)")
        sys.exit(1)

    # Download all tickers
    results = {}

    print(f"\n{'='*60}")
    print(f"Downloading {len(args.tickers)} tickers from {args.source.upper()}")
    print(f"Period: {args.days} days, Interval: {args.interval} minutes")
    print(f"{'='*60}\n")

    for i, ticker in enumerate(args.tickers, 1):
        print(f"[{i}/{len(args.tickers)}] {ticker}")

        # Download data
        df = downloader.download_ticker(ticker, days=args.days, interval=args.interval)

        if df is not None and not df.empty:
            # Format for LEAN
            lean_df = downloader.format_for_lean(df, ticker)

            # Save to file
            filepath = downloader.save_csv(lean_df, ticker, str(args.interval))
            results[ticker] = filepath

        print()

        # Add delay between tickers to be nice to the API
        if i < len(args.tickers):
            time.sleep(1)

    # Summary
    print(f"{'='*60}")
    print(f"✓ Successfully downloaded: {len(results)}/{len(args.tickers)} tickers")
    print(f"✓ Data saved to: {Path(args.data_dir).absolute()}")
    print(f"{'='*60}\n")

    # Exit code
    if len(results) == len(args.tickers):
        print("✓ All downloads successful!")
        sys.exit(0)
    else:
        print(f"⚠️  {len(args.tickers) - len(results)} tickers failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
