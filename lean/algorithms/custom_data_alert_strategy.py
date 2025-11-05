"""
Custom Data + Alert Execution Strategy

This algorithm demonstrates all 4 custom requirements:
1. Custom data provider (YFinance)
2. Universe selection (watchlist of 10 tech stocks)
3. Backtesting on downloaded data
4. Custom execution model (API alerts instead of real trades)

Strategy:
- Simple momentum strategy using 20-period EMA
- Buys when price crosses above EMA (bullish signal)
- Sells when price crosses below EMA (bearish signal)
- Uses equal weighting for portfolio construction

Data:
- 5-minute intraday data from Yahoo Finance
- Data must be downloaded first using scripts/download_yfinance_data.py

Execution:
- Generates alerts instead of placing real orders
- Alerts can be sent to custom API endpoint
- Perfect for paper trading or signal generation
"""

import sys
sys.path.append('/Lean/Algorithm')

from AlgorithmImports import *
from custom.data_providers.yfinance_data import YFinanceData
from custom.execution_models.alert_execution_model import AlertExecutionModel


class CustomDataAlertStrategy(QCAlgorithm):
    """
    Momentum strategy using custom YFinance data and alert-based execution
    """

    def Initialize(self):
        """
        Initialize the algorithm
        """
        # =================================================================
        # 1. Basic Setup
        # =================================================================

        # Set backtest period (last month)
        self.SetStartDate(2024, 10, 1)
        self.SetEndDate(2024, 10, 31)

        # Set starting capital
        self.SetCash(100000)

        # Set timezone to market time
        self.SetTimeZone("America/New_York")

        # =================================================================
        # 2. Define Universe (Requirement #2: Watchlist)
        # =================================================================

        # Our watchlist of 10 tech stocks
        self.universe_tickers = [
            "AAPL",   # Apple
            "MSFT",   # Microsoft
            "GOOGL",  # Alphabet
            "AMZN",   # Amazon
            "NVDA",   # NVIDIA
            "TSLA",   # Tesla
            "META",   # Meta
            "AMD",    # AMD
            "INTC",   # Intel
            "NFLX"    # Netflix
        ]

        # =================================================================
        # 3. Add Custom Data (Requirement #1 & #3: YFinance data)
        # =================================================================

        # Dictionary to store symbol objects
        self.symbols = {}

        # Dictionary to store indicators
        self.ema = {}

        # Dictionary to track signal state
        self.signals = {}

        # Add each ticker from our universe
        for ticker in self.universe_tickers:
            # Add custom data subscription
            # This uses our YFinanceData class to read downloaded data
            symbol = self.AddData(
                YFinanceData,
                ticker,
                Resolution.Minute  # 5-minute data
            ).Symbol

            # Store the symbol
            self.symbols[ticker] = symbol

            # Create EMA indicator for this symbol
            # 20-period EMA for momentum signal
            self.ema[ticker] = self.EMA(symbol, 20, Resolution.Minute)

            # Initialize signal tracking
            self.signals[ticker] = {
                "position": 0,  # -1 = short/none, 0 = none, 1 = long
                "last_signal": None
            }

            self.Debug(f"Added {ticker} to universe with EMA(20)")

        # =================================================================
        # 4. Set Custom Execution Model (Requirement #4: API Alerts)
        # =================================================================

        # Option A: Dry run (just log alerts)
        self.SetExecution(AlertExecutionModel(dry_run=True))

        # Option B: Send to your custom API (uncomment to use)
        # self.SetExecution(AlertExecutionModel(
        #     api_url="https://your-api.com/trading/alerts",
        #     api_key="your_api_key_here",
        #     dry_run=False
        # ))

        # =================================================================
        # 5. Portfolio Settings
        # =================================================================

        # Equal weight for each position
        self.equal_weight = 1.0 / len(self.universe_tickers)

        # Rebalancing frequency (daily at market open)
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.AfterMarketOpen("AAPL", 30),  # 30 min after open
            self.Rebalance
        )

        # Log initialization
        self.Debug("="*60)
        self.Debug("Custom Data + Alert Strategy Initialized")
        self.Debug(f"Universe: {len(self.universe_tickers)} tech stocks")
        self.Debug(f"Period: {self.StartDate} to {self.EndDate}")
        self.Debug(f"Data Source: YFinance (5-minute bars)")
        self.Debug(f"Execution: Alert-based (no real trades)")
        self.Debug("="*60)

    def OnData(self, data: Slice):
        """
        Process incoming data and generate signals

        Args:
            data: Slice containing data for all subscribed symbols
        """
        # Process each ticker in our universe
        for ticker in self.universe_tickers:
            symbol = self.symbols[ticker]

            # Skip if we don't have data for this symbol
            if symbol not in data:
                continue

            # Skip if indicator not ready
            if not self.ema[ticker].IsReady:
                continue

            # Get current price and EMA
            current_price = data[symbol].Close
            ema_value = self.ema[ticker].Current.Value

            # Generate signal
            signal = self._generate_signal(ticker, current_price, ema_value)

            # If signal changed, update target
            if signal != self.signals[ticker]["last_signal"]:
                self._update_target(ticker, signal, current_price)
                self.signals[ticker]["last_signal"] = signal

    def _generate_signal(self, ticker: str, price: float, ema: float) -> int:
        """
        Generate trading signal based on price vs EMA

        Args:
            ticker: Stock ticker
            price: Current price
            ema: EMA value

        Returns:
            1 = bullish (buy), -1 = bearish (sell), 0 = neutral
        """
        # Bullish: price above EMA
        if price > ema:
            return 1

        # Bearish: price below EMA
        elif price < ema:
            return -1

        # Neutral
        else:
            return 0

    def _update_target(self, ticker: str, signal: int, price: float):
        """
        Update portfolio target based on signal

        Args:
            ticker: Stock ticker
            signal: Trading signal (-1, 0, 1)
            price: Current price
        """
        symbol = self.symbols[ticker]

        if signal == 1:
            # Bullish signal: set target to equal weight
            self.SetHoldings(symbol, self.equal_weight)
            self.Debug(f"📈 {ticker}: BULLISH signal @ ${price:.2f} (above EMA)")

        elif signal == -1:
            # Bearish signal: liquidate
            if self.Portfolio[symbol].Invested:
                self.Liquidate(symbol)
                self.Debug(f"📉 {ticker}: BEARISH signal @ ${price:.2f} (below EMA)")

        # Note: The AlertExecutionModel will intercept these and send alerts
        # instead of placing real orders

    def Rebalance(self):
        """
        Periodic rebalancing logic

        Called daily 30 minutes after market open
        """
        # Count positions
        invested_count = sum(1 for t in self.universe_tickers
                           if self.Portfolio[self.symbols[t]].Invested)

        # Log portfolio status
        self.Debug(f"Rebalance check: {invested_count}/{len(self.universe_tickers)} positions")

    def OnEndOfAlgorithm(self):
        """
        Final summary at end of backtest
        """
        self.Debug("="*60)
        self.Debug("Backtest Completed")
        self.Debug("="*60)

        # Portfolio summary
        self.Debug(f"Final Portfolio Value: ${self.Portfolio.TotalPortfolioValue:,.2f}")
        self.Debug(f"Cash: ${self.Portfolio.Cash:,.2f}")
        self.Debug(f"Holdings: ${self.Portfolio.TotalHoldingsValue:,.2f}")

        # Calculate returns
        initial_cash = 100000
        final_value = self.Portfolio.TotalPortfolioValue
        total_return = ((final_value - initial_cash) / initial_cash) * 100

        self.Debug(f"Total Return: {total_return:.2f}%")

        # Position summary
        self.Debug("")
        self.Debug("Final Positions:")
        for ticker in self.universe_tickers:
            symbol = self.symbols[ticker]
            holding = self.Portfolio[symbol]

            if holding.Invested:
                pnl = holding.UnrealizedProfit
                pnl_pct = (pnl / holding.HoldingsCost) * 100 if holding.HoldingsCost != 0 else 0
                self.Debug(f"  {ticker}: {holding.Quantity} shares @ ${holding.AveragePrice:.2f} "
                          f"(P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")

        self.Debug("="*60)


# ==============================================================================
# Alternative: Framework-Based Implementation
# ==============================================================================
"""
For more sophisticated strategies, you can use LEAN's Algorithm Framework:

class FrameworkStrategy(QCAlgorithm):

    def Initialize(self):
        # Universe selection
        self.SetUniverseSelection(ManualUniverseSelectionModel([
            Symbol.Create(ticker, SecurityType.Base, Market.USA)
            for ticker in ["AAPL", "MSFT", "GOOGL", ...]
        ]))

        # Alpha model (signal generation)
        self.SetAlpha(MyCustomAlphaModel())

        # Portfolio construction
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())

        # Execution model (our custom alert model)
        self.SetExecution(AlertExecutionModel(dry_run=True))

        # Risk management
        self.SetRiskManagement(MaximumDrawdownPercentPerSecurity(0.05))

This provides more modularity but requires more setup.
"""
