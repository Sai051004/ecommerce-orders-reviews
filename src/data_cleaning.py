"""Load and clean the raw orders dataset, then summarize revenue by category."""

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


def add_order_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the orders with a revenue column (qty * unit_price)."""
    with_revenue = df.copy()
    with_revenue["revenue"] = with_revenue["qty"] * with_revenue["unit_price"]
    return with_revenue


def calculate_category_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Total revenue per category, highest first.

    Orders with a missing category are kept as their own <NA> group so their
    revenue is not silently dropped. Ties are ordered alphabetically by category.
    """
    orders = add_order_revenue(df)
    return (
        orders.groupby("category", dropna=False)["revenue"]
        .sum()
        .reset_index(name="total_revenue")
        .sort_values("total_revenue", ascending=False, kind="stable")
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    orders_path = Path(__file__).resolve().parent.parent / "data" / "orders.json"
    df = load_orders(str(orders_path))

    normalized_df = normalize_orders(df)
    cleaned_df = fill_missing_categories(normalized_df)
    category_revenue = calculate_category_revenue(cleaned_df)

    print("\nCleaned Orders:")
    print(cleaned_df.to_string(index=False))

    print("\nRevenue by Category:")
    print(category_revenue.to_string(index=False))
