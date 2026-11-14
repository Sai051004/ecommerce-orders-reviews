"""Load and clean the raw orders dataset, then report revenue by category and top sellers."""

import json
from pathlib import Path

import pandas as pd

TEXT_COLUMNS = ["product", "category"]
NUMERIC_COLUMNS = ["qty", "unit_price"]


def load_orders(file_path: str) -> pd.DataFrame:
    """Read a JSON list of orders into a DataFrame."""
    with open(file_path, encoding="utf-8") as f:
        orders = json.load(f)
    return pd.DataFrame(orders)


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def _normalize_text(values: pd.Series) -> pd.Series:
    """Collapse whitespace, trim, and capitalize each word. Blank values become pd.NA.

    Only the first letter of each space-separated word is capitalized, so
    "men's shoes" becomes "Men's Shoes" (str.title() would give "Men'S Shoes").
    """
    cleaned = (
        values.astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.lower()
        .str.replace(
            r"(^| )(\W*)(\w)",
            lambda m: m.group(1) + m.group(2) + m.group(3).upper(),
            regex=True,
        )
    )
    return cleaned.replace("", pd.NA)


def _validated_numbers(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return `columns` converted to numbers.

    Raises ValueError naming the affected orders if any value is missing,
    non-numeric or negative, so no order is silently dropped from a total.
    """
    _require_columns(df, columns)
    numbers = df[columns].apply(pd.to_numeric, errors="coerce")
    invalid = numbers.isna().any(axis=1) | (numbers < 0).any(axis=1)
    if invalid.any():
        if "order_id" in df.columns:
            bad_orders = df.loc[invalid, "order_id"].tolist()
        else:
            bad_orders = df.index[invalid].tolist()
        raise ValueError(f"Missing, non-numeric or negative {columns} in orders: {bad_orders}")
    return numbers


def normalize_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the orders with normalized product and category values.

    Raises ValueError if the same order_id appears more than once, since a
    duplicated order would be counted twice in revenue and quantities.
    """
    _require_columns(df, TEXT_COLUMNS)
    if "order_id" in df.columns:
        duplicated = df.loc[df["order_id"].duplicated(), "order_id"]
        if not duplicated.empty:
            raise ValueError(f"Duplicate order_id values: {sorted(set(duplicated))}")

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
    """Return a copy of the orders with a revenue column (qty * unit_price).

    Raises ValueError if any qty or unit_price is missing, non-numeric or negative.
    """
    numbers = _validated_numbers(df, NUMERIC_COLUMNS)
    with_revenue = df.copy()
    with_revenue["revenue"] = numbers["qty"] * numbers["unit_price"]
    return with_revenue


def calculate_category_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Total revenue per category, highest first.

    Orders with a missing category are kept as their own <NA> group so their
    revenue is not silently dropped. Ties are ordered alphabetically by category.
    """
    _require_columns(df, ["category"])
    orders = add_order_revenue(df)
    return (
        orders.groupby("category", dropna=False)["revenue"]
        .sum()
        .reset_index(name="total_revenue")
        .sort_values("total_revenue", ascending=False, kind="stable")
        .reset_index(drop=True)
    )


def get_top_selling_products(df: pd.DataFrame, top_n: int = 2) -> pd.DataFrame:
    """Top `top_n` products by total quantity sold, highest first.

    Ties are ordered alphabetically by product name. Orders with a missing
    product name are excluded, since they cannot be attributed to a product.
    If `top_n` exceeds the number of products, all products are returned.
    Raises ValueError if any qty is missing, non-numeric or negative.
    """
    if isinstance(top_n, bool) or not isinstance(top_n, int):
        raise TypeError(f"top_n must be an integer, got {type(top_n).__name__}")
    if top_n < 1:
        raise ValueError(f"top_n must be at least 1, got {top_n}")
    _require_columns(df, ["product"])

    orders = df.assign(qty=_validated_numbers(df, ["qty"])["qty"])
    return (
        orders.groupby("product", dropna=True)["qty"]
        .sum()
        .reset_index(name="total_quantity")
        .sort_values(["total_quantity", "product"], ascending=[False, True])
        .head(top_n)
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    orders_path = Path(__file__).resolve().parent.parent / "data" / "orders.json"
    df = load_orders(str(orders_path))

    normalized_df = normalize_orders(df)
    cleaned_df = fill_missing_categories(normalized_df)
    category_revenue = calculate_category_revenue(cleaned_df)
    top_products = get_top_selling_products(cleaned_df, top_n=2)

    print("\nCleaned Orders:")
    print(cleaned_df.to_string(index=False))

    print("\nRevenue by Category:")
    print(category_revenue.to_string(index=False))

    print("\nTop 2 Best-Selling Products:")
    print(top_products.to_string(index=False))
