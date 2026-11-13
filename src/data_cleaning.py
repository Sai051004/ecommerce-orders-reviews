"""Load the raw orders dataset and normalize its text columns."""

import json

import pandas as pd

TEXT_COLUMNS = ["product", "category"]


def load_orders(file_path: str) -> pd.DataFrame:
    """Read a JSON list of orders into a DataFrame."""
    with open(file_path, encoding="utf-8") as f:
        orders = json.load(f)
    return pd.DataFrame(orders)


def _normalize_text(values: pd.Series) -> pd.Series:
    """Collapse whitespace, trim, and title-case text. Blank values become pd.NA."""
    cleaned = (
        values.astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.title()
    )
    return cleaned.replace("", pd.NA)


def normalize_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the orders with normalized product and category values."""
    missing_columns = [col for col in TEXT_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    normalized = df.copy()
    for column in TEXT_COLUMNS:
        normalized[column] = _normalize_text(normalized[column])
    return normalized
