"""Load the raw orders dataset, normalize its text columns, and fill missing categories."""

import json
from pathlib import Path

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


def fill_missing_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing categories from other orders of the same product.

    A category is filled only when the product has exactly one known category.
    Products with no known category, or with conflicting ones, stay missing.
    Expects a DataFrame already passed through normalize_orders().
    """
    filled = df.copy()

    known = filled.dropna(subset=["product", "category"])
    category_counts = known.groupby("product")["category"].nunique()
    unambiguous_products = category_counts[category_counts == 1].index

    product_to_category = (
        known[known["product"].isin(unambiguous_products)]
        .drop_duplicates(subset="product")
        .set_index("product")["category"]
    )

    inferred = filled["product"].map(product_to_category).astype("string")
    filled["category"] = filled["category"].fillna(inferred)
    return filled


if __name__ == "__main__":
    orders_path = Path(__file__).resolve().parent.parent / "data" / "orders.json"
    df = load_orders(str(orders_path))
    df = normalize_orders(df)
    df = fill_missing_categories(df)
    print(df.to_string(index=False))
