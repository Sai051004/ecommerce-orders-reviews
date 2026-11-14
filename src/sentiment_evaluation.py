"""Evaluate LLM-generated sentiment labels against reference labels."""

import json
from pathlib import Path

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


def calculate_accuracy(df: pd.DataFrame) -> float:
    """Fraction of reviews whose predicted label matches the reference (0 to 1)."""
    if df.empty:
        raise ValueError("Cannot calculate accuracy: the dataset has no reviews")

    correct = is_correct(df)
    return float(correct.sum() / len(df))


if __name__ == "__main__":
    reviews_path = Path(__file__).resolve().parent.parent / "data" / "reviews.json"
    reviews = load_reviews(str(reviews_path))

    correct = is_correct(reviews)
    accuracy = calculate_accuracy(reviews)

    results = reviews[["review_id", "reference_label", "predicted_label"]].assign(
        correct=correct
    )
    print("Per-review results:")
    print(results.to_string(index=False))

    print(f"\nTotal Reviews: {len(reviews)}")
    print(f"Correct Predictions: {correct.sum()}")
    print(f"Incorrect Predictions: {(~correct).sum()}")
    print(f"Accuracy: {accuracy:.2%}")
