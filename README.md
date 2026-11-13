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
│   └── __init__.py
├── .gitignore
└── README.md
```

## Requirements

- Python 3
- pandas

Setup and run instructions will be added as the implementation progresses.
