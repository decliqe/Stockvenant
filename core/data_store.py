"""
Data Store - Central state manager for the framework
Implements Observer pattern for reactive data updates.
"""

import pandas as pd

from typing import Optional, List
from PyQt6.QtCore import QObject, pyqtSignal


class DataStore(QObject):


    # Signals for reactive updates
    data_loaded = pyqtSignal(pd.DataFrame)  # Emitted when dataset is loaded
    data_updated = pyqtSignal(pd.DataFrame)  # Emitted when data changes
    symbols_changed = pyqtSignal(list)  # Emitted when available symbols change
    error_occurred = pyqtSignal(str)  # Emitted on errors

    def __init__(self):
        super().__init__()
        self._df: Optional[pd.DataFrame] = None
        self._symbols: List[str] = []
        self._date_range: tuple = (None, None)

    @property
    def df(self) -> Optional[pd.DataFrame]:
        """Get current dataset."""
        return self._df

    @property
    def symbols(self) -> List[str]:
        """Get list of available symbols."""
        return self._symbols.copy()

    @property
    def date_range(self) -> tuple:
        """Get date range (min_date, max_date)."""
        return self._date_range

    def load_from_csv(self, filepath: str) -> bool:

        try:
            # Read CSV
            df = pd.read_csv(filepath)

            # Validate structure
            if df.empty:
                raise ValueError("CSV file is empty")

            if 'Date' not in df.columns:
                raise ValueError("CSV must have 'Date' column")

            # Parse dates
            df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')
            df.set_index('Date', inplace=True)

            # Clean numeric columns (remove commas from price data)
            for col in df.columns:
                if col != 'Date':
                    df[col] = df[col].apply(self._clean_numeric_value)

            # Update store
            self._df = df
            self._extract_symbols()
            self._update_date_range()

            # Notify subscribers
            self.data_loaded.emit(df)
            self.symbols_changed.emit(self._symbols)

            print(f"[DataStore] Loaded {len(df)} rows, {len(self._symbols)} symbols from {filepath}")
            return True

        except Exception as e:
            error_msg = f"Failed to load data: {str(e)}"
            print(f"[DataStore] ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def update_data(self, df: pd.DataFrame) -> bool:
        """
        Update dataset with new data (hot reload).

        Args:
            df: New DataFrame to load

        Returns:
            True if successful
        """
        try:
            if df.empty:
                raise ValueError("Cannot update with empty data")

            # Ensure Date column exists
            if 'Date' not in df.columns:
                raise ValueError("Data must have 'Date' column")

            # Parse dates if needed
            if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')

            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')
            df.set_index('Date', inplace=True)

            # Clean numeric columns (remove commas from price data)
            for col in df.columns:
                if col != 'Date':
                    df[col] = df[col].apply(self._clean_numeric_value)

            # Update store
            self._df = df
            self._extract_symbols()
            self._update_date_range()

            # Notify subscribers
            self.data_updated.emit(df)
            self.symbols_changed.emit(self._symbols)

            print(f"[DataStore] Updated: {len(df)} rows, {len(self._symbols)} symbols")
            return True

        except Exception as e:
            error_msg = f"Failed to update data: {str(e)}"
            print(f"[DataStore] ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def merge_with_new_data(self, new_df: pd.DataFrame) -> bool:
        """
        Merge new data with existing data (for incremental updates).

        Args:
            new_df: New DataFrame to merge

        Returns:
            True if successful
        """
        try:
            if self._df is None:
                return self.update_data(new_df)

            # Ensure both have Date as index
            if 'Date' in new_df.columns:
                new_df['Date'] = pd.to_datetime(new_df['Date'], format='%d-%m-%Y', errors='coerce')
                new_df = new_df.set_index('Date')

            # Merge (new data overwrites old on conflicts)
            merged = self._df.combine_first(new_df)
            merged = merged.sort_index()

            # Update store
            self._df = merged
            self._extract_symbols()
            self._update_date_range()

            # Notify subscribers
            self.data_updated.emit(merged)
            self.symbols_changed.emit(self._symbols)

            print(f"[DataStore] Merged: {len(merged)} rows, {len(self._symbols)} symbols")
            return True

        except Exception as e:
            error_msg = f"Failed to merge data: {str(e)}"
            print(f"[DataStore] ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def get_symbol_data(self, symbol: str) -> Optional[pd.Series]:
        """
        Get data for a specific symbol.

        Args:
            symbol: Stock symbol name

        Returns:
            Series with price data or None
        """
        if self._df is None or symbol not in self._df.columns:
            return None
        return self._df[symbol]

    def has_symbol(self, symbol: str) -> bool:
        """Check if symbol exists in dataset."""
        return symbol in self._symbols

    def _extract_symbols(self):
        """Extract available symbols from dataframe."""
        if self._df is None:
            self._symbols = []
            return

        # Get all columns except Date (if it's still a column)
        self._symbols = [col for col in self._df.columns if col != 'Date']

    def _clean_numeric_value(self, value):
        """
        Clean and convert numeric value to float, handling commas and empty values.

        Args:
            value: Value to clean (can be string, float, or None)

        Returns:
            Float value or None if invalid
        """
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

    def _update_date_range(self):
        """Update the date range tuple."""
        if self._df is None or self._df.empty:
            self._date_range = (None, None)
            return

        self._date_range = (self._df.index.min(), self._df.index.max())

    def clear(self):
        """Clear all data."""
        self._df = None
        self._symbols = []
        self._date_range = (None, None)
        self.data_updated.emit(pd.DataFrame())
        self.symbols_changed.emit([])
        print("[DataStore] Cleared all data")

    def get_statistics(self) -> dict:
        """Get statistics about current dataset."""
        if self._df is None:
            return {
                'rows': 0,
                'symbols': 0,
                'date_range': 'N/A',
                'missing_data': 0
            }

        return {
            'rows': len(self._df),
            'symbols': len(self._symbols),
            'date_range': f"{self._date_range[0].strftime('%Y-%m-%d')} to {self._date_range[1].strftime('%Y-%m-%d')}",
            'missing_data': self._df.isna().sum().sum()
        }

