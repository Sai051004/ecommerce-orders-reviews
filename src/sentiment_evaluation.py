"""Evaluate LLM-generated sentiment labels against reference labels."""

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

LABEL_COLUMNS = ["reference_label", "predicted_label"]
ERROR_COLUMNS = ["review_id", "review_text", *LABEL_COLUMNS]
SENTIMENT_LABELS = ["positive", "negative", "neutral", "mixed"]


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


def analyze_errors(df: pd.DataFrame) -> pd.DataFrame:
    """Return only the misclassified reviews, with their text and both labels.

    Returns an empty DataFrame with the same columns when every prediction is correct.
    """
    missing_columns = [col for col in ERROR_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    wrong = ~is_correct(df)
    return df.loc[wrong, ERROR_COLUMNS].reset_index(drop=True)


def _validated_labels(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Return (reference, predicted) labels, normalized and checked against SENTIMENT_LABELS.

    Raises ValueError for empty input, missing columns, or any unsupported/missing label,
    so no review is silently left out of the metrics.
    """
    if df.empty:
        raise ValueError("Cannot calculate metrics: the dataset has no reviews")
    missing_columns = [col for col in LABEL_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    labels = {}
    for column in LABEL_COLUMNS:
        values = df[column].astype("string").str.strip().str.lower()
        unexpected = values[~values.isin(SENTIMENT_LABELS)]
        if not unexpected.empty:
            raise ValueError(
                f"Unsupported values in {column}: {unexpected.unique().tolist()}. "
                f"Expected one of {SENTIMENT_LABELS}"
            )
        labels[column] = values.tolist()
    return labels["reference_label"], labels["predicted_label"]


def calculate_classification_metrics(df: pd.DataFrame) -> dict:
    """Accuracy plus per-class, macro and weighted precision, recall and F1.

    Classes are evaluated in the fixed order of SENTIMENT_LABELS. A metric that is
    undefined (e.g. precision for a class that is never predicted) is reported as 0.
    """
    reference, predicted = _validated_labels(df)

    precision, recall, f1, support = precision_recall_fscore_support(
        reference, predicted, labels=SENTIMENT_LABELS, zero_division=0
    )
    per_class = {
        label: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i, label in enumerate(SENTIMENT_LABELS)
    }

    averages = {}
    for average in ("macro", "weighted"):
        avg_precision, avg_recall, avg_f1, _ = precision_recall_fscore_support(
            reference, predicted, labels=SENTIMENT_LABELS, average=average, zero_division=0
        )
        averages[average] = {
            "precision": float(avg_precision),
            "recall": float(avg_recall),
            "f1": float(avg_f1),
        }

    return {
        "labels": list(SENTIMENT_LABELS),
        "accuracy": calculate_accuracy(df),
        "per_class": per_class,
        "macro": averages["macro"],
        "weighted": averages["weighted"],
    }


def generate_confusion_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Counts of reference (rows) vs predicted (columns) labels, in SENTIMENT_LABELS order."""
    reference, predicted = _validated_labels(df)
    matrix = confusion_matrix(reference, predicted, labels=SENTIMENT_LABELS)
    return pd.DataFrame(
        matrix,
        index=pd.Index(SENTIMENT_LABELS, name="actual"),
        columns=pd.Index(SENTIMENT_LABELS, name="predicted"),
    )


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

    errors = analyze_errors(reviews)
    print("\nMisclassified Reviews:")
    print(errors.to_string(index=False))

    metrics = calculate_classification_metrics(reviews)
    per_class = pd.DataFrame(metrics["per_class"]).T
    per_class["support"] = per_class["support"].astype(int)
    averages = pd.DataFrame({"macro": metrics["macro"], "weighted": metrics["weighted"]}).T

    print("\nPer-Class Metrics:")
    print(per_class.to_string(float_format="{:.4f}".format))
    print("\nAveraged Metrics:")
    print(averages.to_string(float_format="{:.4f}".format))
    print(f"\nAccuracy: {metrics['accuracy']:.4f}")

    print("\nConfusion Matrix (rows = actual, columns = predicted):")
    print(generate_confusion_matrix(reviews).to_string())
