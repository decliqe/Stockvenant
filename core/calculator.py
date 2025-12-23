"""
Handles all calculation logic for stock trading profit/loss.
"""

import pandas as pd
from datetime import date
from dataclasses import dataclass
from typing import Optional


@dataclass
class TradeResult:
    """Result of a trade calculation."""
    stock: str
    quantity: float
    purchase_date: pd.Timestamp
    sell_date: pd.Timestamp
    purchase_price: float
    sell_price: float
    purchase_total: float
    sell_total: float
    profit: float


class InputError(Exception):
    """Raised when user input is invalid."""
    pass


class DataError(Exception):
    """Raised when data is missing or invalid."""
    pass


class StockCalculator:
    """
    Pure calculation logic for stock trading.
    No UI dependencies - can be used standalone or tested independently.
    """

    def __init__(self, data_store):
        """
        Initialize calculator with data store.

        Args:
            data_store: DataStore instance containing stock data
        """
        self.data_store = data_store

    def compute_trade(self, stock: str, quantity: float,
                     purchase_date: date, sell_date: date) -> TradeResult:
        """
        Compute profit/loss for a single stock trade.

        Args:
            stock: Stock symbol name
            quantity: Number of shares to trade
            purchase_date: Date to buy
            sell_date: Date to sell

        Returns:
            TradeResult with all calculation details

        Raises:
            InputError: If inputs are invalid
            DataError: If stock data is missing
        """
        # Validate inputs
        self._validate_inputs(stock, quantity, purchase_date, sell_date)

        # Get stock data
        df = self.data_store.df
        if df is None:
            raise DataError("No data loaded")

        if stock not in df.columns:
            raise DataError(f"Stock '{stock}' not found in dataset")

        # Convert dates to timestamps
        purchase_ts = pd.Timestamp(purchase_date)
        sell_ts = pd.Timestamp(sell_date)

        # Find prices
        purchase_price = self._get_price_on_date(df, stock, purchase_ts)
        sell_price = self._get_price_on_date(df, stock, sell_ts)

        # Calculate totals
        purchase_total = purchase_price * quantity
        sell_total = sell_price * quantity
        profit = sell_total - purchase_total

        return TradeResult(
            stock=stock,
            quantity=quantity,
            purchase_date=purchase_ts,
            sell_date=sell_ts,
            purchase_price=purchase_price,
            sell_price=sell_price,
            purchase_total=purchase_total,
            sell_total=sell_total,
            profit=profit
        )

    def compute_multiple_trades(self, stocks: list, quantity: float,
                                purchase_date: date, sell_date: date) -> dict:
        """
        Compute trades for multiple stocks.

        Args:
            stocks: List of stock symbols
            quantity: Number of shares per stock
            purchase_date: Date to buy
            sell_date: Date to sell

        Returns:
            Dict mapping stock names to TradeResult objects
        """
        results = {}

        for stock in stocks:
            try:
                result = self.compute_trade(stock, quantity, purchase_date, sell_date)
                results[stock] = result
            except (InputError, DataError) as e:
                results[stock] = e

        return results

    def _validate_inputs(self, stock: str, quantity: float,
                        purchase_date: date, sell_date: date):
        """Validate input parameters."""
        if not stock or not isinstance(stock, str):
            raise InputError("Stock symbol must be a non-empty string")

        if quantity <= 0:
            raise InputError("Quantity must be positive")

        if not isinstance(purchase_date, date) or not isinstance(sell_date, date):
            raise InputError("Dates must be date objects")

        if purchase_date >= sell_date:
            raise InputError("Purchase date must be before sell date")

        # Check if dates are within dataset range
        date_range = self.data_store.date_range
        if date_range[0] is not None:
            if pd.Timestamp(purchase_date) < date_range[0]:
                raise InputError(f"Purchase date {purchase_date} is before dataset start {date_range[0].date()}")

            if pd.Timestamp(sell_date) > date_range[1]:
                raise InputError(f"Sell date {sell_date} is after dataset end {date_range[1].date()}")

    def _clean_numeric_value(self, value) -> Optional[float]:

        if pd.isna(value):
            return None

        # Convert to string and remove commas
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            if not value:
                return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_price_on_date(self, df: pd.DataFrame, stock: str,
                          target_date: pd.Timestamp) -> float:
        """
        Get stock price on a specific date.
        Uses forward fill if exact date not available.

        Args:
            df: DataFrame with stock data
            stock: Stock symbol
            target_date: Target date

        Returns:
            Price on that date

        Raises:
            DataError: If price cannot be determined
        """
        try:
            # Try exact match first
            if target_date in df.index:
                price = df.loc[target_date, stock]
                if pd.notna(price):
                    cleaned_price = self._clean_numeric_value(price)
                    if cleaned_price is not None:
                        return cleaned_price

            # Use forward fill (get nearest previous date with data)
            mask = df.index <= target_date
            valid_dates = df[mask].index

            if len(valid_dates) == 0:
                raise DataError(f"No data available on or before {target_date.date()}")

            nearest_date = valid_dates[-1]
            price = df.loc[nearest_date, stock]

            if pd.isna(price):
                raise DataError(f"Price for {stock} is missing on {nearest_date.date()}")

            cleaned_price = self._clean_numeric_value(price)
            if cleaned_price is None:
                raise DataError(f"Invalid price format for {stock} on {nearest_date.date()}")

            return cleaned_price

        except Exception as e:
            raise DataError(f"Failed to get price for {stock} on {target_date.date()}: {str(e)}")

