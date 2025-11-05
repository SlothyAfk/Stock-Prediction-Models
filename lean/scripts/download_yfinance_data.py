#!/usr/bin/env python3
"""
YFinance Data Downloader for LEAN

Downloads historical intraday data from Yahoo Finance and converts it to
LEAN-compatible CSV format for backtesting.

Features:
- Downloads 5-minute interval data
- Handles timezone conversions (market time to UTC)
- Saves in LEAN's expected CSV format
- Supports batch downloads for multiple tickers
- Includes data validation and error handling

Usage:
    python download_yfinance_data.py
    python download_yfinance_data.py --tickers AAPL MSFT GOOGL
    python download_yfinance_data.py --period 2mo --interval 5m
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd
import pytz
import yfinance as yf


class LEANDataDownloader:
    """Downloads market data from Yahoo Finance and formats it for LEAN"""

    def __init__(self, data_dir: str = "./data/custom"):
        """
        Initialize the downloader

        Args:
            data_dir: Directory to save downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Market timezone (NYSE/NASDAQ)
        self.market_tz = pytz.timezone('America/New_York')
        self.utc_tz = pytz.UTC

    def download_ticker(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "5m"
    ) -> pd.DataFrame:
        """
        Download data for a single ticker

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            period: Data period ('1mo', '2mo', '3mo', '1y', etc.)
            interval: Data interval ('1m', '2m', '5m', '15m', '1h', '1d')

        Returns:
            DataFrame with OHLCV data
        """
        print(f"Downloading {ticker} data ({period}, {interval} intervals)...")

        try:
            # Download from yfinance
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period, interval=interval)

            if df.empty:
                print(f"  ⚠️  No data returned for {ticker}")
                return None

            print(f"  ✓ Downloaded {len(df)} bars")
            return df

        except Exception as e:
            print(f"  ✗ Error downloading {ticker}: {e}")
            return None

    def format_for_lean(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Convert yfinance DataFrame to LEAN CSV format

        LEAN expects: DateTime,Open,High,Low,Close,Volume
        DateTime must be in UTC and format: YYYYMMDD HH:MM:SS

        Args:
            df: Raw yfinance DataFrame
            ticker: Ticker symbol

        Returns:
            Formatted DataFrame ready for LEAN
        """
        # Copy to avoid modifying original
        lean_df = df.copy()

        # Reset index to get datetime as column
        lean_df = lean_df.reset_index()

        # Convert timezone-aware datetime to UTC
        if lean_df['Datetime'].dt.tz is not None:
            # Already timezone-aware, convert to UTC
            lean_df['Datetime'] = lean_df['Datetime'].dt.tz_convert('UTC')
        else:
            # Assume market timezone, localize then convert to UTC
            lean_df['Datetime'] = lean_df['Datetime'].dt.tz_localize(self.market_tz)
            lean_df['Datetime'] = lean_df['Datetime'].dt.tz_convert('UTC')

        # Remove timezone info for LEAN (LEAN expects naive UTC datetimes)
        lean_df['Datetime'] = lean_df['Datetime'].dt.tz_localize(None)

        # Format datetime as LEAN expects: YYYYMMDD HH:MM:SS
        lean_df['DateTime'] = lean_df['Datetime'].dt.strftime('%Y%m%d %H:%M:%S')

        # Select and rename columns to match LEAN format
        lean_df = lean_df[['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Round prices to reasonable precision
        price_cols = ['Open', 'High', 'Low', 'Close']
        lean_df[price_cols] = lean_df[price_cols].round(4)

        # Ensure volume is integer
        lean_df['Volume'] = lean_df['Volume'].astype(int)

        # Remove any rows with NaN values
        lean_df = lean_df.dropna()

        print(f"  ✓ Formatted {len(lean_df)} bars for LEAN")
        print(f"  Date range: {lean_df['DateTime'].iloc[0]} to {lean_df['DateTime'].iloc[-1]} UTC")

        return lean_df

    def save_csv(self, df: pd.DataFrame, ticker: str) -> Path:
        """
        Save formatted data to CSV file

        Args:
            df: Formatted DataFrame
            ticker: Ticker symbol

        Returns:
            Path to saved file
        """
        # Create ticker subdirectory
        ticker_dir = self.data_dir / ticker.lower()
        ticker_dir.mkdir(parents=True, exist_ok=True)

        # Save with date-based filename
        filename = f"{ticker.lower()}_5min.csv"
        filepath = ticker_dir / filename

        # Save without index, no header (LEAN reads column positions)
        df.to_csv(filepath, index=False, header=False)

        file_size = filepath.stat().st_size / 1024  # KB
        print(f"  ✓ Saved to {filepath} ({file_size:.1f} KB)")

        return filepath

    def download_universe(
        self,
        tickers: List[str],
        period: str = "1mo",
        interval: str = "5m"
    ) -> dict:
        """
        Download data for multiple tickers

        Args:
            tickers: List of ticker symbols
            period: Data period
            interval: Data interval

        Returns:
            Dictionary of {ticker: filepath} for successful downloads
        """
        results = {}

        print(f"\n{'='*60}")
        print(f"Downloading {len(tickers)} tickers")
        print(f"Period: {period}, Interval: {interval}")
        print(f"{'='*60}\n")

        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker}")

            # Download data
            df = self.download_ticker(ticker, period, interval)

            if df is not None and not df.empty:
                # Format for LEAN
                lean_df = self.format_for_lean(df, ticker)

                # Save to file
                filepath = self.save_csv(lean_df, ticker)
                results[ticker] = filepath

            print()  # Blank line between tickers

        # Summary
        print(f"{'='*60}")
        print(f"✓ Successfully downloaded: {len(results)}/{len(tickers)} tickers")
        print(f"✓ Data saved to: {self.data_dir.absolute()}")
        print(f"{'='*60}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download market data from Yahoo Finance for LEAN backtesting"
    )

    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "INTC", "NFLX"],
        help="List of ticker symbols to download (default: 10 tech stocks)"
    )

    parser.add_argument(
        "--period",
        default="1mo",
        help="Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max (default: 1mo)"
    )

    parser.add_argument(
        "--interval",
        default="5m",
        help="Data interval: 1m, 2m, 5m, 15m, 30m, 1h, 1d (default: 5m)"
    )

    parser.add_argument(
        "--data-dir",
        default="./data/custom",
        help="Directory to save downloaded data (default: ./data/custom)"
    )

    args = parser.parse_args()

    # Create downloader
    downloader = LEANDataDownloader(data_dir=args.data_dir)

    # Download all tickers
    results = downloader.download_universe(
        tickers=args.tickers,
        period=args.period,
        interval=args.interval
    )

    # Exit with success/failure code
    if len(results) == len(args.tickers):
        print("✓ All downloads successful!")
        sys.exit(0)
    else:
        print(f"⚠️  {len(args.tickers) - len(results)} tickers failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
