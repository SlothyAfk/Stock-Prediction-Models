#!/usr/bin/env python3
"""
YFinance Data Downloader - HOST SYSTEM VERSION

This script runs on your HOST system (where yfinance works) and downloads
data to the lean/data/custom/ directory which is mounted into the Docker pod.

The pod can then read this data for backtesting without hitting Yahoo's
Docker container blocking.

Usage:
    # On your host system (NOT in Docker pod)
    cd ~/Stock-Prediction-Models/lean
    python3 download_data_host.py

    # Or with custom tickers
    python3 download_data_host.py --tickers AAPL MSFT GOOGL
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    import pytz
    import yfinance as yf
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("\nPlease install required packages:")
    print("  pip3 install yfinance pandas pytz")
    sys.exit(1)


class HostDataDownloader:
    """Downloads market data on host system for Docker pod consumption"""

    def __init__(self, data_dir: str = "./data/custom"):
        """
        Initialize the downloader

        Args:
            data_dir: Directory to save downloaded data (relative to lean/)
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
        Download data for a single ticker using Ticker().history()

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            period: Data period ('1mo', '2mo', '3mo', '1y', etc.)
            interval: Data interval ('1m', '2m', '5m', '15m', '1h', '1d')

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        print(f"  Downloading {ticker} ({period}, {interval})...")

        try:
            # Use Ticker().history() - same as their production code
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period, interval=interval)

            if df.empty:
                print(f"    ✗ No data returned for {ticker}")
                return None

            print(f"    ✓ Downloaded {len(df)} bars")
            return df

        except Exception as e:
            print(f"    ✗ Error: {type(e).__name__}: {str(e)[:80]}")
            return None

    def format_for_lean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert yfinance DataFrame to LEAN CSV format

        LEAN expects: DateTime,Open,High,Low,Close,Volume
        DateTime format: YYYYMMDD HH:MM:SS (UTC, no timezone info)

        Args:
            df: Raw yfinance DataFrame

        Returns:
            Formatted DataFrame ready for LEAN
        """
        lean_df = df.copy().reset_index()

        # Convert timezone to UTC
        if lean_df['Date'].dt.tz is not None:
            lean_df['Date'] = lean_df['Date'].dt.tz_convert('UTC')
        else:
            # Assume market timezone if naive
            lean_df['Date'] = lean_df['Date'].dt.tz_localize(self.market_tz).dt.tz_convert('UTC')

        # Remove timezone info (LEAN expects naive UTC)
        lean_df['Date'] = lean_df['Date'].dt.tz_localize(None)

        # Format as LEAN expects: YYYYMMDD HH:MM:SS
        lean_df['DateTime'] = lean_df['Date'].dt.strftime('%Y%m%d %H:%M:%S')

        # Select columns in LEAN order
        lean_df = lean_df[['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Round prices to 4 decimal places
        for col in ['Open', 'High', 'Low', 'Close']:
            lean_df[col] = lean_df[col].round(4)

        # Ensure volume is integer
        lean_df['Volume'] = lean_df['Volume'].astype(int)

        # Remove any NaN rows
        lean_df = lean_df.dropna()

        return lean_df

    def save_csv(self, df: pd.DataFrame, ticker: str, interval: str) -> Path:
        """
        Save formatted data to CSV file

        Args:
            df: Formatted DataFrame
            ticker: Ticker symbol
            interval: Data interval (for filename)

        Returns:
            Path to saved file
        """
        # Create ticker subdirectory
        ticker_dir = self.data_dir / ticker.lower()
        ticker_dir.mkdir(parents=True, exist_ok=True)

        # Filename format: {ticker}_{interval}.csv
        interval_str = interval.replace('m', 'min').replace('h', 'hour').replace('d', 'day')
        filename = f"{ticker.lower()}_{interval_str}.csv"
        filepath = ticker_dir / filename

        # Save without index, no header (LEAN reads by column position)
        df.to_csv(filepath, index=False, header=False)

        file_size = filepath.stat().st_size / 1024  # KB
        print(f"    ✓ Saved {len(df)} bars to {filepath} ({file_size:.1f} KB)")
        print(f"    Date range: {df['DateTime'].iloc[0]} to {df['DateTime'].iloc[-1]} UTC")

        return filepath

    def download_universe(
        self,
        tickers: list,
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

        print(f"\n{'='*70}")
        print(f"YFinance Data Download - HOST SYSTEM")
        print(f"{'='*70}")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"Period: {period}, Interval: {interval}")
        print(f"Output: {self.data_dir.absolute()}")
        print(f"{'='*70}\n")

        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker}")

            # Download data
            df = self.download_ticker(ticker, period, interval)

            if df is not None and not df.empty:
                # Format for LEAN
                lean_df = self.format_for_lean(df)

                # Save to file
                filepath = self.save_csv(lean_df, ticker, interval)
                results[ticker] = filepath

            print()  # Blank line

        # Summary
        print(f"{'='*70}")
        print(f"Summary: {len(results)}/{len(tickers)} tickers downloaded successfully")
        if len(results) > 0:
            print(f"\n✓ Data saved to: {self.data_dir.absolute()}")
            print(f"✓ Docker pod can now access this data at: /Lean/data/custom/")
            print(f"\nNext steps:")
            print(f"  1. Verify data in pod: ls -lh /Lean/data/custom/")
            print(f"  2. Run backtest: cd /Lean/Launcher/bin/Debug")
            print(f"  3. Execute: dotnet QuantConnect.Lean.Launcher.dll")
        else:
            print(f"\n✗ All downloads failed. Check your internet connection and try again.")
        print(f"{'='*70}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download market data from Yahoo Finance on HOST system for Docker pod"
    )

    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "INTC", "NFLX"],
        help="List of ticker symbols (default: 10 tech stocks)"
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
        help="Data directory relative to lean/ (default: ./data/custom)"
    )

    args = parser.parse_args()

    # Verify we're in the right directory
    if not Path("docker-compose.yml").exists():
        print("ERROR: Please run this script from the lean/ directory:")
        print("  cd ~/Stock-Prediction-Models/lean")
        print("  python3 download_data_host.py")
        sys.exit(1)

    # Create downloader
    downloader = HostDataDownloader(data_dir=args.data_dir)

    # Download all tickers
    results = downloader.download_universe(
        tickers=args.tickers,
        period=args.period,
        interval=args.interval
    )

    # Exit with appropriate code
    sys.exit(0 if len(results) == len(args.tickers) else 1)


if __name__ == "__main__":
    main()
