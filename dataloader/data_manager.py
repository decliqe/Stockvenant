"""
Data Manager - Enhanced Version
Central manager for handling multiple data sources and caching.
"""

import pandas as pd
from typing import Dict, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime


class DataManager(QObject):

    # Signals
    data_updated = pyqtSignal(str, pd.DataFrame)  # symbol, data
    cache_cleared = pyqtSignal()
    merge_completed = pyqtSignal(pd.DataFrame)  # merged dataframe
    error_occurred = pyqtSignal(str)  # error message

    def __init__(self):
        super().__init__()
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.loaders: Dict[str, object] = {}
        self.master_df: Optional[pd.DataFrame] = None
        self.auto_merge_enabled = True

    def register_loader(self, name: str, loader):
        """Register a data loader."""
        self.loaders[name] = loader
        print(f"[DataManager] ✓ Registered loader: {name}")

    def get_loader(self, name: str):
        """Get a registered loader by name."""
        return self.loaders.get(name)

    def get_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get cached data for a symbol."""
        return self.data_cache.get(symbol)

    def update_data(self, symbol: str, data: pd.DataFrame):
        """Update cached data for a symbol."""
        if data.empty:
            print(f"[DataManager] ⚠ Empty data for {symbol}")
            return

        try:
            if symbol =="multiple":
                for col in data.columns:
                    if col != 'Date':
                        symbol_data = data[['Date', col]].copy()
                        symbol_data = symbol_data.rename(columns={col: col})
                        self.data_cache[col] = symbol_data
                        print(f"[DataManager] ✓ Cached {col}: {len(symbol_data)} rows")
                if self.auto_merge_enabled and len(self.data_cache) > 0:
                    self.merge_symbol_data()
                return
            # Validate data structure
            if 'Date' not in data.columns or symbol not in data.columns:
                raise ValueError(f"Invalid data structure for {symbol}")

            self.data_cache[symbol] = data
            print(f"[DataManager] ✓ Cached {symbol}: {len(data)} rows")
            self.data_updated.emit(symbol, data)

            # Auto-merge if enabled
            if self.auto_merge_enabled and len(self.data_cache) > 0:
                self.merge_symbol_data()

        except Exception as e:
            error_msg = f"Error updating data for {symbol}: {str(e)}"
            print(f"[DataManager] ✗ {error_msg}")
            self.error_occurred.emit(error_msg)

    def merge_symbol_data(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """Merge data from multiple symbols into framework format."""
        try:
            if symbols is None:
                symbols = list(self.data_cache.keys())

            if not symbols:
                return pd.DataFrame()

            merged = None

            for symbol in symbols:
                data = self.data_cache.get(symbol)
                if data is None or data.empty:
                    continue

                if 'Date' not in data.columns or symbol not in data.columns:
                    print(f"[DataManager] ⚠ Skipping {symbol}: invalid structure")
                    continue

                symbol_data = data[['Date', symbol]].copy()

                if merged is None:
                    merged = symbol_data
                else:
                    merged = pd.merge(merged, symbol_data, on='Date', how='outer')

            if merged is not None and not merged.empty:
                # Sort and format dates
                merged['Date'] = pd.to_datetime(merged['Date'], format='%d-%m-%Y', errors='coerce')
                merged = merged.dropna(subset=['Date'])
                merged = merged.sort_values('Date')
                merged['Date'] = merged['Date'].dt.strftime('%d-%m-%Y')

                self.master_df = merged
                print(f"[DataManager] ✓ Merged {len(symbols)} symbols → {len(merged)} rows")
                self.merge_completed.emit(merged)
            else:
                merged = pd.DataFrame()

            return merged

        except Exception as e:
            error_msg = f"Error merging data: {str(e)}"
            print(f"[DataManager] ✗ {error_msg}")
            self.error_occurred.emit(error_msg)
            return pd.DataFrame()

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cached data (specific symbol or all)."""
        try:
            if symbol:
                if symbol in self.data_cache:
                    del self.data_cache[symbol]
                    print(f"[DataManager] ✓ Cleared cache for {symbol}")
                    self.merge_symbol_data()  # Re-merge remaining symbols
            else:
                self.data_cache.clear()
                self.master_df = None
                print("[DataManager] ✓ Cleared all cache")
                self.cache_cleared.emit()
        except Exception as e:
            error_msg = f"Error clearing cache: {str(e)}"
            print(f"[DataManager] ✗ {error_msg}")
            self.error_occurred.emit(error_msg)

    def get_cached_symbols(self) -> List[str]:
        """Get list of all cached symbols."""
        return sorted(list(self.data_cache.keys()))

    def save_master_to_csv(self, filename: str) -> bool:
        """Save master DataFrame to CSV."""
        try:
            if self.master_df is None or self.master_df.empty:
                self.error_occurred.emit("No data to save")
                return False

            self.master_df.to_csv(filename, index=False)
            print(f"[DataManager] ✓ Saved {len(self.master_df)} rows to {filename}")
            return True

        except Exception as e:
            error_msg = f"Error saving CSV: {str(e)}"
            print(f"[DataManager] ✗ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def load_master_from_csv(self, filename: str) -> pd.DataFrame:
        """Load master DataFrame from CSV."""
        try:
            df = pd.read_csv(filename)

            if df.empty or 'Date' not in df.columns:
                raise ValueError("Invalid CSV format")

            self.master_df = df

            # Update cache with individual symbols
            for col in df.columns:
                if col != 'Date':
                    symbol_data = df[['Date', col]].copy()
                    symbol_data = symbol_data.rename(columns={col: col})
                    self.data_cache[col] = symbol_data

            print(f"[DataManager] ✓ Loaded {len(df)} rows, {len(df.columns)-1} symbols from {filename}")
            self.merge_completed.emit(df)
            return df

        except Exception as e:
            error_msg = f"Error loading CSV: {str(e)}"
            print(f"[DataManager] ✗ {error_msg}")
            self.error_occurred.emit(error_msg)
            return pd.DataFrame()

    def get_date_range(self) -> tuple:
        """Get date range of cached data."""
        if self.master_df is None or self.master_df.empty:
            return (None, None)

        try:
            dates = pd.to_datetime(self.master_df['Date'], format='%d-%m-%Y', errors='coerce')
            return (dates.min(), dates.max())
        except Exception:
            return (None, None)

    def get_statistics(self) -> Dict:
        """Get detailed statistics about cached data."""
        stats = {
            'cached_symbols': len(self.data_cache),
            'symbol_list': self.get_cached_symbols(),
            'master_rows': len(self.master_df) if self.master_df is not None else 0,
            'master_columns': len(self.master_df.columns) - 1 if self.master_df is not None else 0,
            'auto_merge': self.auto_merge_enabled,
        }

        date_range = self.get_date_range()
        if date_range[0] is not None:
            stats['earliest_date'] = date_range[0].strftime('%Y-%m-%d')
            stats['latest_date'] = date_range[1].strftime('%Y-%m-%d')
            stats['date_span_days'] = (date_range[1] - date_range[0]).days
        else:
            stats['earliest_date'] = 'N/A'
            stats['latest_date'] = 'N/A'
            stats['date_span_days'] = 0

        # Per-symbol statistics
        stats['symbol_details'] = {}
        for symbol, data in self.data_cache.items():
            stats['symbol_details'][symbol] = {
                'rows': len(data),
                'last_update': datetime.now().strftime('%H:%M:%S')
            }

        return stats
