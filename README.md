# E-Commerce Orders & Reviews

Coding assignment covering data cleaning, aggregation, LLM evaluation, and knowledge graphs.

## Part A: Coding (current scope)

Clean a messy orders dataset, then compute:

1. Total revenue per category.
2. The top 2 best-selling products by quantity.

Known data issues in the raw dataset:

- Product names use inconsistent casing (`Wireless Mouse` vs `wireless mouse`).
- Category names use inconsistent casing (`electronics` vs `Electronics`).
- One order (`O3`, `Yoga Mat`) has an empty category.

## Data

`data/orders.json` holds the original five orders exactly as given in the assignment.
This raw file is never modified. Cleaning happens in code.

## Project structure

```text
ecommerce-orders-reviews/
├── data/
│   └── orders.json   # raw input, unmodified
├── src/
│   ├── __init__.py
│   └── data_cleaning.py   # load + normalize orders
├── .gitignore
└── README.md
```

## Requirements

- Python 3
- pandas

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install pandas
```

## Usage

Print the normalized orders (run from the project root):

```bash
python -m src.data_cleaning
```

Normalization trims and collapses whitespace and title-cases `product` and `category`.
Blank categories become missing values (`<NA>`); they are not filled in yet.
