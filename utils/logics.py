from dataclasses import dataclass
from datetime import date as Date
from typing import Optional, List, Tuple

import pandas as pd

# Cache for the loaded dataset to avoid re-reading the CSV repeatedly.
_DF_CACHE: Optional[pd.DataFrame] = None


@dataclass
class TradeResult:
    #Container for a single-stock trade calculation result.
    stock: str
    quantity: float
    purchase_date: pd.Timestamp
    sell_date: pd.Timestamp
    purchase_price: float
    sell_price: float
    purchase_total: float
    sell_total: float
    profit: float


class DataError(Exception):
    """Raised when the dataset is missing or malformed."""


class InputError(Exception):
    """Raised when user input is invalid (e.g., quantity <= 0, dates out of range)."""



def load_dataset(csv_path: str) -> pd.DataFrame:
    global _DF_CACHE
    if _DF_CACHE is not None:
        return _DF_CACHE

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError as e:
        raise DataError(f"Dataset not found at path: {csv_path}") from e

    if 'Date' not in df.columns:
        raise DataError("CSV must contain a 'Date' column")

    # Parse dates and set index
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if df['Date'].isna().all():
        raise DataError("Failed to parse any dates in 'Date' column")

    df = df.dropna(subset=['Date']).copy()
    df = df.set_index('Date').sort_index()

    # Coerce all non-date columns to numeric; strip commas and stray chars first
    for col in df.columns:
        cleaned = (
            df[col]
            .astype(str)
            .str.replace(r"[^0-9.\-]", "", regex=True)  # remove commas, quotes, spaces, etc.
        )
        df[col] = pd.to_numeric(cleaned, errors='coerce')

    # Optional check
    if df.dropna(how='all', axis=1).shape[1] == 0:
        raise DataError("Dataset has no usable numeric columns after cleaning")

    # Cache and return (now outside the loop)
    _DF_CACHE = df
    return _DF_CACHE


def get_stocks(df: pd.DataFrame) -> List[str]:
    """Return the list of stock columns (all columns in df)."""
    return list(df.columns)


def _to_ts(d: Date | pd.Timestamp) -> pd.Timestamp:
    """Helper: Convert Python date or pandas Timestamp to pandas Timestamp (normalized)."""
    if isinstance(d, pd.Timestamp):
        return d.normalize()
    return pd.Timestamp(d)


def get_price_on_or_before(df: pd.DataFrame, stock: str, target_date: Date | pd.Timestamp) -> Tuple[pd.Timestamp, float]:

    if stock not in df.columns:
        raise InputError(f"Unknown stock column: {stock}")

    ts = _to_ts(target_date)

    series = df[stock]


    series_nonan = series.dropna()
    actual_date = series_nonan.index.asof(ts)

    if pd.isna(actual_date):
        # This means timestamps are earlier than the first available date with a non-NaN price
        raise InputError("No trade price available.")

    price = float(series_nonan.loc[actual_date])
    return actual_date, price


def compute_trade(
    df: pd.DataFrame,
    stock: str,
    quantity: float,
    purchase_date: Date | pd.Timestamp,
    sell_date: Date | pd.Timestamp,
) -> TradeResult:

    if quantity is None or quantity <= 0:
        raise InputError("Quantity must be greater than 0")

    p_ts = _to_ts(purchase_date)
    s_ts = _to_ts(sell_date)

    if s_ts < p_ts:
        raise InputError("Sell date cannot be earlier than purchase date")

    p_actual_date, p_price = get_price_on_or_before(df, stock, p_ts)
    s_actual_date, s_price = get_price_on_or_before(df, stock, s_ts)

    purchase_total = p_price * quantity
    sell_total = s_price * quantity
    profit = sell_total - purchase_total

    return TradeResult(
        stock=stock,
        quantity=quantity,
        purchase_date=p_actual_date,
        sell_date=s_actual_date,
        purchase_price=p_price,
        sell_price=s_price,
        purchase_total=purchase_total,
        sell_total=sell_total,
        profit=profit,
    )
