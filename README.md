# E-Commerce Orders & Reviews

Coding assignment for the Duck Creek Technologies Associate Software Engineer (AI) role.

**Part A** is a Python and pandas data-processing pipeline that:

- Loads raw e-commerce orders from JSON.
- Normalizes inconsistent product and category names.
- Infers missing categories from existing records.
- Calculates total revenue by category.
- Identifies the top 2 best-selling products by quantity.

**Part B** (LLM evaluation and knowledge graph) is not yet implemented. See [Future work](#future-work).

## Problem statement

> Clean this messy orders dataset (inconsistent casing, missing category) and compute:
>
> 1. Total revenue per category.
> 2. The top 2 best-selling products by quantity.

The raw data in [`data/orders.json`](data/orders.json) has three problems:

| Issue | Example |
|---|---|
| Inconsistent product casing | `Wireless Mouse` (O1) vs `wireless mouse` (O2) |
| Inconsistent category casing | `electronics` (O1) vs `Electronics` (O2) |
| Missing category | O3 `Yoga Mat` has category `""` |

## Project structure

```text
ecommerce-orders-reviews/
├── data/
│   └── orders.json        # raw input: the five original orders, never modified
├── src/
│   ├── __init__.py
│   └── data_cleaning.py   # Part A pipeline: load, clean, revenue, top sellers
├── .gitignore
└── README.md
```
