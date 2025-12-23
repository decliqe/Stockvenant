"""
YFinance Data Loader
Fetches stock data from yfinance and converts to framework CSV format.
"""

import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict
import queue
from PyQt6.QtCore import QObject, pyqtSignal


class YFinanceDataLoader(QObject):
    """
    Data loader for fetching stock data from yfinance.
    Converts data to the format expected by the calculation framework.

    The framework expects CSV format with columns:
    Date, Natural_Gas, Crude_oil, Copper, Bitcoin, Platinum, Ethereum,
    S&P_500, Nasdaq_100, Apple, Tesla, Microsoft, Silver, Google, Nvidia,
    Berkshire, Netflix, Amazon, Meta, Gold

    Each row contains Date and price data for all available symbols.
    """

    # Signals for async communication with UI
    data_received = pyqtSignal(pd.DataFrame, str)  # data, symbol
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str, int)  # message, percentage

    def __init__(self):
        super().__init__()
        self.data_queue = queue.Queue()
        self._cached_data: Dict[str, pd.DataFrame] = {}

    def fetch_historical_data(self, symbol: str, start_date: str,
                             end_date: str, interval: str = '1d') -> pd.DataFrame:
        """
        Fetch historical stock data from yfinance.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL' for Apple)
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval (1d, 1h, 5m, etc.)

        Returns:
            DataFrame with columns: Date, Close (price for the symbol)
        """
        try:
            self.progress_update.emit(f"Fetching {symbol}...", 10)

            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)

            if data.empty:
                error_msg = f"No data found for {symbol} between {start_date} and {end_date}"
                self.error_occurred.emit(error_msg)
                return pd.DataFrame()

            self.progress_update.emit(f"Processing {symbol}...", 70)

            # Convert to framework format
            formatted_data = self._format_single_symbol(data, symbol)

            # Cache the data
            self._cached_data[symbol] = formatted_data

            self.progress_update.emit(f"Completed {symbol}", 100)
            self.data_received.emit(formatted_data, symbol)

            return formatted_data

        except Exception as e:
            error_msg = f"Error fetching data for {symbol}: {str(e)}"
            self.error_occurred.emit(error_msg)
            return pd.DataFrame()

    def fetch_multiple_symbols(self, symbols: List[str], start_date: str,
                              end_date: str, interval: str = '1d') -> pd.DataFrame:
        """
        Fetch data for multiple symbols and combine into framework format.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval

        Returns:
            DataFrame in framework CSV format with all symbols as columns
        """
        try:
            all_data = {}
            total = len(symbols)

            for idx, symbol in enumerate(symbols):
                progress = int((idx / total) * 100)
                self.progress_update.emit(f"Fetching {symbol} ({idx+1}/{total})...", progress)

                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval=interval)

                if not data.empty:
                    # Extract close prices
                    all_data[symbol] = data['Close']
                else:
                    self.error_occurred.emit(f"No data for {symbol}")

            if not all_data:
                self.error_occurred.emit("No data fetched for any symbol")
                return pd.DataFrame()

            # Combine all symbols into single DataFrame
            combined = pd.DataFrame(all_data)

            # Reset index to make Date a column
            combined.reset_index(inplace=True)
            combined.rename(columns={'index': 'Date'}, inplace=True)

            # Format dates to match framework: d-m-YYYY
            combined['Date'] = pd.to_datetime(combined['Date']).dt.strftime('%d-%m-%Y')

            self.progress_update.emit("Data fetch complete", 100)
            self.data_received.emit(combined, "multiple")

            return combined

        except Exception as e:
            error_msg = f"Error fetching multiple symbols: {str(e)}"
            self.error_occurred.emit(error_msg)
            return pd.DataFrame()

    def fetch_realtime_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch the most recent data point for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with latest data point
        """
        try:
            ticker = yf.Ticker(symbol)
            # Get today's data with 1-minute interval
            data = ticker.history(period='1d', interval='1m')

            if data.empty:
                # Fallback to last available day
                data = ticker.history(period='5d', interval='1d')
                if data.empty:
                    error_msg = f"No real-time data available for {symbol}"
                    self.error_occurred.emit(error_msg)
                    return pd.DataFrame()

            # Get the latest row
            latest = data.tail(1)
            formatted_data = self._format_single_symbol(latest, symbol)

            self.data_received.emit(formatted_data, symbol)
            return formatted_data

        except Exception as e:
            error_msg = f"Error fetching real-time data for {symbol}: {str(e)}"
            self.error_occurred.emit(error_msg)
            return pd.DataFrame()


    def _format_single_symbol(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Convert yfinance data for a single symbol to framework format.

        Args:
            data: Raw yfinance DataFrame
            symbol: Stock symbol name

        Returns:
            DataFrame with Date and symbol price columns
        """
        formatted = pd.DataFrame()

        # Reset index to get date as column
        data = data.reset_index()

        # Format date to match framework: dd-mm-yyyy
        formatted['Date'] = pd.to_datetime(data['Date']).dt.strftime('%d-%m-%Y')

        # Use Close price as the main price
        formatted[symbol] = data['Close'].round(2)

        return formatted

    def save_to_csv(self, data: pd.DataFrame, filename: str):
        """
        Save data to CSV file in framework format.

        Args:
            data: DataFrame to save
            filename: Output file path
        """
        try:
            data.to_csv(filename, index=False)
            self.progress_update.emit(f"Saved to {filename}", 100)
        except Exception as e:
            error_msg = f"Error saving to CSV: {str(e)}"
            self.error_occurred.emit(error_msg)

    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get cached data for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Cached DataFrame or None if not cached
        """
        return self._cached_data.get(symbol)

    def clear_cache(self):
        """Clear all cached data."""
        self._cached_data.clear()
        self.progress_update.emit("Cache cleared", 100)

