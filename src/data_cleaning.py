"""Load the raw orders dataset and normalize its text columns."""

import json

import pandas as pd


def load_orders(file_path: str) -> pd.DataFrame:
    """Read a JSON list of orders into a DataFrame."""
    with open(file_path, encoding="utf-8") as f:
        orders = json.load(f)
    return pd.DataFrame(orders)
