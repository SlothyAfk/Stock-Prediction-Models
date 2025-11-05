"""
Example LEAN Trading Algorithm - Buy and Hold SPY

This is a simple example algorithm that demonstrates the basic structure
of a LEAN algorithm. It implements a buy-and-hold strategy for the SPY ETF.

For more examples, see:
https://github.com/QuantConnect/Lean/tree/master/Algorithm.Python
"""

from AlgorithmImports import *


class BuyAndHoldSPY(QCAlgorithm):
    """
    Buy and Hold SPY Algorithm

    This algorithm demonstrates:
    - Initialization of an algorithm
    - Adding equity data
    - Setting a benchmark
    - Simple buy-and-hold logic
    - Portfolio management
    - Logging
    """

    def Initialize(self):
        """
        Initialize the algorithm settings and add securities.
        This method is called once at the start of the algorithm.
        """
        # Set the algorithm start and end dates
        self.SetStartDate(2020, 1, 1)   # Start date: January 1, 2020
        self.SetEndDate(2023, 12, 31)    # End date: December 31, 2023

        # Set the initial cash for the algorithm
        self.SetCash(100000)  # $100,000

        # Add the SPY equity with daily resolution
        # SPY is the S&P 500 ETF
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Set the benchmark to SPY (to compare our performance)
        self.SetBenchmark("SPY")

        # Set brokerage model (default is fine for backtesting)
        # self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # Set warmup period (optional - for indicators that need historical data)
        # self.SetWarmUp(20)

        # Initialize variables
        self.invested = False

        # Log initialization
        self.Debug(f"Algorithm initialized. Start: {self.StartDate}, End: {self.EndDate}")
        self.Debug(f"Initial Cash: ${self.Portfolio.Cash:,.2f}")

    def OnData(self, data: Slice):
        """
        OnData event is the primary entry point for your algorithm.
        Each time we receive data, this method is called.

        Args:
            data: Slice object containing the data for all subscribed securities
        """
        # Check if we have data for SPY
        if not data.ContainsKey(self.spy):
            return

        # If we're not invested yet, buy SPY
        if not self.invested:
            # Get the current price
            price = data[self.spy].Close

            # Calculate how many shares we can buy
            quantity = int(self.Portfolio.Cash / price)

            # Place a market order
            self.MarketOrder(self.spy, quantity)

            # Mark as invested
            self.invested = True

            # Log the trade
            self.Debug(f"BUY: {quantity} shares of SPY at ${price:.2f}")
            self.Debug(f"Total cost: ${quantity * price:,.2f}")

    def OnOrderEvent(self, orderEvent: OrderEvent):
        """
        Event handler for order events.
        Called whenever an order is filled, cancelled, or has an error.

        Args:
            orderEvent: OrderEvent containing details about the order
        """
        if orderEvent.Status == OrderStatus.Filled:
            self.Debug(f"Order filled: {orderEvent.Symbol} - " +
                      f"Quantity: {orderEvent.FillQuantity}, " +
                      f"Price: ${orderEvent.FillPrice:.2f}")

    def OnEndOfAlgorithm(self):
        """
        Called at the end of the algorithm.
        Useful for final calculations and logging.
        """
        self.Debug("="*50)
        self.Debug("Algorithm Completed")
        self.Debug("="*50)
        self.Debug(f"Final Portfolio Value: ${self.Portfolio.TotalPortfolioValue:,.2f}")
        self.Debug(f"Cash: ${self.Portfolio.Cash:,.2f}")
        self.Debug(f"Holdings: ${self.Portfolio.TotalHoldingsValue:,.2f}")

        # Calculate returns
        initial_cash = 100000
        final_value = self.Portfolio.TotalPortfolioValue
        total_return = ((final_value - initial_cash) / initial_cash) * 100

        self.Debug(f"Total Return: {total_return:.2f}%")
        self.Debug("="*50)


class MovingAverageCrossover(QCAlgorithm):
    """
    Moving Average Crossover Algorithm

    This algorithm demonstrates a simple moving average crossover strategy:
    - Buy when the fast MA crosses above the slow MA
    - Sell when the fast MA crosses below the slow MA

    This is a more advanced example showing indicator usage.
    """

    def Initialize(self):
        """Initialize the algorithm"""
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Add SPY
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Create moving averages
        self.fast_period = 50
        self.slow_period = 200

        self.fast_ma = self.SMA(self.spy, self.fast_period, Resolution.Daily)
        self.slow_ma = self.SMA(self.spy, self.slow_period, Resolution.Daily)

        # Warm up the indicators
        self.SetWarmUp(self.slow_period)

        self.Debug(f"Initialized Moving Average Crossover Strategy")
        self.Debug(f"Fast MA: {self.fast_period} days, Slow MA: {self.slow_period} days")

    def OnData(self, data: Slice):
        """Event handler for new data"""
        # Wait for indicators to be ready
        if self.IsWarmingUp or not self.fast_ma.IsReady or not self.slow_ma.IsReady:
            return

        # Get current values
        fast_value = self.fast_ma.Current.Value
        slow_value = self.slow_ma.Current.Value

        # Trading logic
        if not self.Portfolio.Invested:
            # Buy signal: fast MA crosses above slow MA
            if fast_value > slow_value:
                self.SetHoldings(self.spy, 1.0)
                self.Debug(f"BUY: Fast MA ({fast_value:.2f}) > Slow MA ({slow_value:.2f})")

        else:
            # Sell signal: fast MA crosses below slow MA
            if fast_value < slow_value:
                self.Liquidate(self.spy)
                self.Debug(f"SELL: Fast MA ({fast_value:.2f}) < Slow MA ({slow_value:.2f})")

    def OnEndOfAlgorithm(self):
        """Final statistics"""
        self.Debug("="*50)
        self.Debug("Moving Average Crossover Completed")
        self.Debug("="*50)
        self.Debug(f"Final Portfolio Value: ${self.Portfolio.TotalPortfolioValue:,.2f}")

        initial_cash = 100000
        final_value = self.Portfolio.TotalPortfolioValue
        total_return = ((final_value - initial_cash) / initial_cash) * 100

        self.Debug(f"Total Return: {total_return:.2f}%")
        self.Debug("="*50)


# ==============================================================================
# To use one of these algorithms:
# ==============================================================================
#
# 1. Choose which algorithm to run (BuyAndHoldSPY or MovingAverageCrossover)
#
# 2. Update your config/config.json:
#    "algorithm-type-name": "BuyAndHoldSPY"
#    "algorithm-location": "/Lean/Algorithm/example_algorithm.py"
#
# 3. Run with docker-compose:
#    docker-compose up
#
# ==============================================================================
