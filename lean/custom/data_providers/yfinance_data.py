"""
YFinance Custom Data Provider for LEAN

This module provides a custom data class that allows LEAN to read
market data downloaded from Yahoo Finance.

Usage in your algorithm:
    from custom.data_providers.yfinance_data import YFinanceData

    def Initialize(self):
        # Add custom data subscription
        self.AddData(YFinanceData, "AAPL", Resolution.Minute)
"""

from AlgorithmImports import *
from datetime import datetime


class YFinanceData(PythonData):
    """
    Custom data class for reading YFinance-downloaded CSV files

    CSV Format expected (no header):
        DateTime,Open,High,Low,Close,Volume
        20240101 09:30:00,150.25,150.50,150.10,150.40,1000000

    This class tells LEAN:
    1. Where to find the data file (GetSource)
    2. How to parse each line (Reader)
    """

    def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
        """
        Tell LEAN where to find the data file

        Args:
            config: Subscription configuration (contains symbol, resolution, etc.)
            date: The date for which we need data
            isLiveMode: Whether running in live mode or backtest

        Returns:
            SubscriptionDataSource with file location and format
        """
        # Get the ticker symbol (lowercase for file path)
        symbol = config.Symbol.Value.lower()

        # Build path to CSV file
        # Format: data/custom/{symbol}/{symbol}_5min.csv
        source = f"/Lean/data/custom/{symbol}/{symbol}_5min.csv"

        # Return source configuration
        # FileFormat.Csv tells LEAN this is a CSV file
        # TransportMedium.LocalFile tells LEAN to read from local filesystem
        return SubscriptionDataSource(source, SubscriptionTransportMedium.LocalFile)

    def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool):
        """
        Parse a line from the CSV file and return a data point

        CSV Format: DateTime,Open,High,Low,Close,Volume
        Example: 20240101 09:30:00,150.25,150.50,150.10,150.40,1000000

        Args:
            config: Subscription configuration
            line: Single line from the CSV file
            date: The date being processed
            isLiveMode: Whether running in live mode

        Returns:
            YFinanceData object with parsed values, or None if parsing fails
        """
        # Skip empty lines
        if not line or line.strip() == "":
            return None

        try:
            # Split the CSV line
            data = line.split(',')

            # Ensure we have all required fields
            if len(data) < 6:
                return None

            # Create a new instance of our data type
            bar = YFinanceData()
            bar.Symbol = config.Symbol

            # Parse datetime (format: YYYYMMDD HH:MM:SS)
            # Example: "20240101 09:30:00"
            datetime_str = data[0].strip()
            bar.Time = datetime.strptime(datetime_str, "%Y%m%d %H:%M:%S")

            # Parse OHLCV data
            bar.Open = float(data[1])
            bar.High = float(data[2])
            bar.Low = float(data[3])
            bar.Close = float(data[4])
            bar.Volume = int(float(data[5]))  # Convert to int (may be scientific notation)

            # Set the value (LEAN uses this for calculations)
            # Typically set to close price
            bar.Value = bar.Close

            # Set the end time (for bar data, this is important)
            # For a 5-minute bar at 09:30, the end time is 09:35
            bar.EndTime = bar.Time

            return bar

        except Exception as e:
            # Log parsing errors for debugging
            # (In production, you might want to handle this more gracefully)
            return None


class YFinanceFiveMinute(YFinanceData):
    """
    Convenience class specifically for 5-minute data

    This is an alias to make the intent clearer in algorithm code:
        self.AddData(YFinanceFiveMinute, "AAPL")
    """
    pass


# ==============================================================================
# Usage Example
# ==============================================================================
"""
In your LEAN algorithm:

from custom.data_providers.yfinance_data import YFinanceData

class MyAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2024, 10, 1)
        self.SetEndDate(2024, 10, 31)
        self.SetCash(100000)

        # Add custom data for AAPL
        self.aapl = self.AddData(YFinanceData, "AAPL").Symbol

        # Or use multiple tickers
        self.tickers = ["AAPL", "MSFT", "GOOGL"]
        self.symbols = {}

        for ticker in self.tickers:
            symbol = self.AddData(YFinanceData, ticker).Symbol
            self.symbols[ticker] = symbol

    def OnData(self, data: Slice):
        # Check if we have AAPL data
        if self.aapl in data:
            aapl_bar = data[self.aapl]
            self.Debug(f"AAPL: O={aapl_bar.Open}, H={aapl_bar.High}, " +
                      f"L={aapl_bar.Low}, C={aapl_bar.Close}, V={aapl_bar.Volume}")

        # Or iterate through all symbols
        for ticker, symbol in self.symbols.items():
            if symbol in data:
                bar = data[symbol]
                # Your trading logic here
                pass
"""
