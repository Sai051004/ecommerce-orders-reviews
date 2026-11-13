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

Print the cleaned orders, revenue by category, and top 2 best-selling products
(run from the project root):

```bash
python -m src.data_cleaning
```

Cleaning runs in two stages:

1. **Normalize**: trim and collapse whitespace and title-case `product` and `category`.
   Blank categories become missing values (`<NA>`).
2. **Fill missing categories**: a missing category is taken from other orders of the
   same product, but only if that product has exactly one known category.
   Products with no known category, or with conflicting ones, stay `<NA>`.

Revenue per order is `qty * unit_price`. Category totals are summed with a pandas
`groupby`, sorted highest first. Orders whose category is still missing are kept
as an `<NA>` row so no revenue is silently dropped.

Best-selling products are ranked by total `qty` per normalized product name, highest
first, with ties broken alphabetically. Orders with a missing product name are
excluded from this ranking because they cannot be attributed to a product.
