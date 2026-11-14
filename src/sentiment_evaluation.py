"""Evaluate LLM-generated sentiment labels against reference labels."""

import json

import pandas as pd

LABEL_COLUMNS = ["reference_label", "predicted_label"]


def load_reviews(file_path: str) -> pd.DataFrame:
    """Read a JSON list of reviews into a DataFrame."""
    with open(file_path, encoding="utf-8") as f:
        reviews = json.load(f)
    return pd.DataFrame(reviews)


def is_correct(df: pd.DataFrame) -> pd.Series:
    """True where the predicted label matches the reference label.

    Labels are compared ignoring case and surrounding whitespace.
    A missing label on either side counts as incorrect.
    """
    missing_columns = [col for col in LABEL_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    reference = df["reference_label"].astype("string").str.strip().str.lower()
    predicted = df["predicted_label"].astype("string").str.strip().str.lower()
    return (reference == predicted).fillna(False).astype(bool)

