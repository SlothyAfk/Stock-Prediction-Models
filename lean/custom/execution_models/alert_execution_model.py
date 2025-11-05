"""
Alert Execution Model for LEAN

This custom execution model replaces actual trade execution with API alerts.
Instead of placing orders with a broker, it sends trade signals to your
custom API endpoint for notifications or external processing.

Use Cases:
- Paper trading with external notification system
- Signal generation for manual trading
- Integration with external trading systems
- Alert-based strategies without automatic execution

Usage in your algorithm:
    from custom.execution_models.alert_execution_model import AlertExecutionModel

    def Initialize(self):
        # Set up alert execution
        self.SetExecution(AlertExecutionModel(
            api_url="https://your-api.com/trading/alerts",
            api_key="your_api_key_here"
        ))
"""

from AlgorithmImports import *
import requests
import json
from datetime import datetime


class AlertExecutionModel(ExecutionModel):
    """
    Custom execution model that sends alerts instead of placing orders

    This model receives PortfolioTarget objects from your algorithm's
    portfolio construction model and converts them into API calls instead
    of brokerage orders.
    """

    def __init__(self, api_url: str = None, api_key: str = None, dry_run: bool = True):
        """
        Initialize the alert execution model

        Args:
            api_url: Your API endpoint URL (e.g., "https://api.example.com/alerts")
            api_key: API authentication key (if required)
            dry_run: If True, only logs alerts without making HTTP calls
        """
        self.api_url = api_url or "http://localhost:8000/trading/alerts"
        self.api_key = api_key
        self.dry_run = dry_run

        # Track sent alerts to avoid duplicates
        self.last_alerts = {}

    def Execute(self, algorithm: QCAlgorithm, targets: List[IPortfolioTarget]) -> List[OrderTicket]:
        """
        Execute the portfolio targets by sending alerts

        This method is called by LEAN when the portfolio construction model
        generates new targets (desired positions).

        Args:
            algorithm: The algorithm instance
            targets: List of portfolio targets (desired positions)

        Returns:
            Empty list (we don't create actual orders)
        """
        # If no targets, nothing to do
        if not targets:
            return []

        # Process each target
        for target in targets:
            self._send_alert(algorithm, target)

        # Return empty list (no actual orders placed)
        return []

    def _send_alert(self, algorithm: QCAlgorithm, target: IPortfolioTarget):
        """
        Send alert for a single portfolio target

        Args:
            algorithm: The algorithm instance
            target: The portfolio target
        """
        symbol = target.Symbol
        target_quantity = target.Quantity

        # Get current holdings
        if algorithm.Portfolio.ContainsKey(symbol):
            current_quantity = algorithm.Portfolio[symbol].Quantity
        else:
            current_quantity = 0

        # Calculate the change needed
        quantity_delta = target_quantity - current_quantity

        # Skip if no change needed
        if quantity_delta == 0:
            return

        # Determine action
        if quantity_delta > 0:
            action = "BUY"
            quantity = abs(quantity_delta)
        else:
            action = "SELL"
            quantity = abs(quantity_delta)

        # Get current price
        if algorithm.Securities.ContainsKey(symbol):
            security = algorithm.Securities[symbol]
            current_price = security.Price
        else:
            current_price = 0

        # Create alert payload
        alert = {
            "timestamp": algorithm.Time.isoformat(),
            "symbol": str(symbol.Value),
            "action": action,
            "quantity": quantity,
            "target_quantity": target_quantity,
            "current_quantity": current_quantity,
            "current_price": current_price,
            "estimated_value": quantity * current_price,
            "algorithm": algorithm.__class__.__name__,
            "metadata": {
                "time_utc": datetime.utcnow().isoformat(),
                "portfolio_value": float(algorithm.Portfolio.TotalPortfolioValue),
                "cash": float(algorithm.Portfolio.Cash)
            }
        }

        # Send the alert
        self._dispatch_alert(algorithm, alert)

    def _dispatch_alert(self, algorithm: QCAlgorithm, alert: dict):
        """
        Dispatch alert to API or log it

        Args:
            algorithm: The algorithm instance
            alert: Alert payload dictionary
        """
        # Create a readable log message
        log_msg = (
            f"🔔 ALERT: {alert['action']} {alert['quantity']} {alert['symbol']} "
            f"@ ${alert['current_price']:.2f} (${alert['estimated_value']:,.2f})"
        )

        # Log to algorithm
        algorithm.Debug(log_msg)

        # If dry run, just log and return
        if self.dry_run:
            algorithm.Debug(f"   [DRY RUN] Would send to: {self.api_url}")
            algorithm.Debug(f"   Payload: {json.dumps(alert, indent=2)}")
            return

        # Send to API
        try:
            headers = {
                "Content-Type": "application/json"
            }

            # Add API key if provided
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Make the HTTP POST request
            response = requests.post(
                self.api_url,
                json=alert,
                headers=headers,
                timeout=5  # 5 second timeout
            )

            # Check response
            if response.status_code == 200:
                algorithm.Debug(f"   ✓ Alert sent successfully")
            else:
                algorithm.Error(f"   ✗ Alert failed: HTTP {response.status_code}")
                algorithm.Error(f"   Response: {response.text}")

        except requests.exceptions.Timeout:
            algorithm.Error(f"   ✗ Alert timeout: {self.api_url}")

        except requests.exceptions.RequestException as e:
            algorithm.Error(f"   ✗ Alert error: {str(e)}")

        except Exception as e:
            algorithm.Error(f"   ✗ Unexpected error sending alert: {str(e)}")


class WebhookExecutionModel(AlertExecutionModel):
    """
    Webhook-based execution model (alias for clarity)

    Same as AlertExecutionModel but with a name that emphasizes
    the webhook pattern.

    Usage:
        self.SetExecution(WebhookExecutionModel(
            api_url="https://webhook.site/your-unique-url"
        ))
    """
    pass


class LogOnlyExecutionModel(AlertExecutionModel):
    """
    Log-only execution model for testing

    This variant only logs signals without making any external calls.
    Useful for development and testing.

    Usage:
        self.SetExecution(LogOnlyExecutionModel())
    """

    def __init__(self):
        """Initialize in dry-run mode with no API"""
        super().__init__(api_url=None, api_key=None, dry_run=True)


# ==============================================================================
# Usage Examples
# ==============================================================================
"""
Example 1: Dry Run (Log Only)
------------------------------
class MyAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Just log alerts, don't send anywhere
        self.SetExecution(AlertExecutionModel(dry_run=True))


Example 2: Send to Your API
----------------------------
class MyAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Send alerts to your custom API
        self.SetExecution(AlertExecutionModel(
            api_url="https://api.myapp.com/trading/signals",
            api_key=os.environ.get("API_KEY"),
            dry_run=False
        ))


Example 3: Webhook Integration
-------------------------------
class MyAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Send to webhook.site for testing
        self.SetExecution(WebhookExecutionModel(
            api_url="https://webhook.site/abc-123-xyz"
        ))


Example 4: Log Only (Explicit)
-------------------------------
class MyAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Explicitly use log-only mode
        self.SetExecution(LogOnlyExecutionModel())


Alert Payload Format:
--------------------
{
    "timestamp": "2024-11-05T10:30:00",
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 100,
    "target_quantity": 100,
    "current_quantity": 0,
    "current_price": 175.50,
    "estimated_value": 17550.00,
    "algorithm": "MyTradingAlgorithm",
    "metadata": {
        "time_utc": "2024-11-05T15:30:00",
        "portfolio_value": 100000.00,
        "cash": 82450.00
    }
}
"""
