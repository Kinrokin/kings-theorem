# File: src/tools/finance_tool.py
"""
AID: /src/tools/finance_tool.py
Proof ID: TOOL-FINANCE-001
Axiom: Integration

Purpose: Connects the Teacher Kernel to external financial data (yfinance).
"""
import logging
from typing import Dict, Optional

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_stock_data(ticker: str) -> Optional[Dict]:
    """
    Fetches the last trading day's closing price and volume for a given ticker.
    This function acts as a formal tool for the Agentic system.
    """
    try:
        stock = yf.Ticker(ticker)
        # Get data for the last 1 day
        history = stock.history(period="1d")

        if history.empty:
            return None

        # Extract the relevant data point (the most recent one)
        latest = history.iloc[-1]

        return {
            "ticker": ticker,
            "last_close": round(latest["Close"], 2),
            "volume": int(latest["Volume"]),
            "currency": stock.info.get("currency", "USD"),
        }
    except Exception as e:
        logger.exception("[FINANCE_TOOL] Error fetching %s: %s", ticker, e)
        return {"error": f"Data lookup failed for {ticker}"}


if __name__ == "__main__":
    # Example test run
    try:
        # If running as a module, ensure global logging is configured
        from src.logging_config import setup_logging as _setup

        _setup()
    except Exception:
        import logging

        logging.basicConfig(level=logging.INFO)
    import json

    # Log JSON for interactive runs
    logger.info(json.dumps(fetch_stock_data("MSFT"), indent=2))
