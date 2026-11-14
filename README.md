# E-Commerce Orders & Reviews

Coding assignment for the Duck Creek Technologies Associate Software Engineer (AI) role.

**Part A** is a Python and pandas data-processing pipeline that:

- Loads raw e-commerce orders from JSON.
- Normalizes inconsistent product and category names.
- Infers missing categories from existing records.
- Calculates total revenue by category.
- Identifies the top 2 best-selling products by quantity.

**Part B1** scores LLM-generated sentiment labels against reference labels. See
[Part B1: Sentiment evaluation](#part-b1-sentiment-evaluation).

**Part B2** (knowledge graph) is not yet implemented. See [Future work](#future-work).

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
│   ├── orders.json              # Part A raw input: the five original orders, never modified
│   └── reviews.json             # Part B1 input: four reviews with reference and LLM labels
├── docs/
│   └── sentiment_error_analysis.md  # Part B1: discussion of misclassified / borderline reviews
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py         # Part A pipeline: load, clean, revenue, top sellers
│   └── sentiment_evaluation.py  # Part B1: sentiment accuracy and error analysis
├── .gitignore
└── README.md
```

## Installation and setup

Requires Python 3 and pandas (developed with Python 3.11 and pandas 3.1).

```bash
git clone https://github.com/Sai051004/ecommerce-orders-reviews.git
cd ecommerce-orders-reviews

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install pandas
```

## Running Part A

From the repository root:

```bash
python -m src.data_cleaning
```

Output:

```text
Cleaned Orders:
order_id        product    category  qty  unit_price
      O1 Wireless Mouse Electronics    3        20.0
      O2 Wireless Mouse Electronics    2        20.0
      O3       Yoga Mat     Fitness    5        15.0
      O4      Desk Lamp        Home    1        25.0
      O5       Yoga Mat     Fitness    2        15.0

Revenue by Category:
   category  total_revenue
    Fitness          105.0
Electronics          100.0
       Home           25.0

Top 2 Best-Selling Products:
       product  total_quantity
      Yoga Mat               7
Wireless Mouse               5
```

## Pipeline

All functions live in [`src/data_cleaning.py`](src/data_cleaning.py). Each returns a new
DataFrame and never modifies its input.

```text
load_orders → normalize_orders → fill_missing_categories ─┬→ calculate_category_revenue
                                                          └→ get_top_selling_products
```

## Data cleaning approach

### Normalizing products and categories (`normalize_orders`)

The same rules apply to `product` and `category`, using vectorized pandas string methods:

1. **Whitespace**: any run of spaces, tabs or newlines collapses to one space, and
   leading/trailing whitespace is removed (`"  wireless   mouse "` → `"wireless mouse"`).
2. **Casing**: values are title-cased (`"wireless mouse"` → `"Wireless Mouse"`,
   `"electronics"` → `"Electronics"`).
3. **Missing values**: empty or whitespace-only values become a true missing value
   (`pd.NA`), never a placeholder string such as `"Unknown"` or `"None"`.

### Filling missing categories (`fill_missing_categories`)

1. Take the orders where both product and category are known.
2. Count the distinct categories for each product.
3. Build a product → category mapping from products with **exactly one** known category
   (here: `Yoga Mat → Fitness`, `Wireless Mouse → Electronics`, `Desk Lamp → Home`).
4. Fill only missing categories from that mapping. Existing categories are never overwritten.

Result: O3 `Yoga Mat` gets `Fitness` from O5.

| Situation | Result |
|---|---|
| Product has one known category | Missing category is filled |
| Product has conflicting categories (e.g. `Fitness` and `Fashion`) | Left missing, not guessed |
| Product has no known category | Left missing |
| Product name is missing | Left missing |

The mapping is learned from the data rather than hardcoded, so it works for any product,
and it only fills a value when the data agrees on a single answer.

### Preserving the original dataset

`data/orders.json` is only read, never written. All cleaning happens on in-memory copies.

## Revenue calculation

For each order, `revenue = qty × unit_price`. Order revenues are summed per category with
a pandas `groupby`, then sorted from highest to lowest (ties alphabetically).

| Category | Calculation | Total revenue |
|---|---|---:|
| Fitness | O3 (5 × 15.00) + O5 (2 × 15.00) | 105.00 |
| Electronics | O1 (3 × 20.00) + O2 (2 × 20.00) | 100.00 |
| Home | O4 (1 × 25.00) | 25.00 |
| **Total** | | **230.00** |

## Top 2 best-selling products

Products are ranked by **total quantity sold**, not by revenue or number of orders. All
orders for the same normalized product name are grouped and their `qty` values summed.

| Rank | Product | Calculation | Quantity |
|---:|---|---|---:|
| 1 | Yoga Mat | O3 (5) + O5 (2) | 7 |
| 2 | Wireless Mouse | O1 (3) + O2 (2) | 5 |

Desk Lamp (1 unit) is third. Ties are broken alphabetically by product name. `top_n`
defaults to 2 and must be a positive integer.

## Assumptions and limitations

- **Normalize before aggregating.** Without it, `Wireless Mouse` and `wireless mouse`
  would be counted as two different products.
- **Only unambiguous categories are inferred.** A missing category is filled only when the
  product has exactly one known category.
- **Conflicts are not resolved automatically.** If a product appears under different
  categories, its missing categories stay missing for manual review.
- **Orders with a missing product name are excluded from the best-seller ranking**, since
  they cannot be attributed to a product.
- **Unresolved categories still count toward revenue.** They appear as an `<NA>` row so no
  revenue is silently dropped.
- **Title case is a simple rule.** It would turn names like `iPhone` into `Iphone`, which
  is fine for this dataset but would need a brand-aware approach in production.
- **Floating-point arithmetic.** Revenue uses floats, which is exact for this dataset's
  prices. A production financial system should use integer cents or `decimal.Decimal`
  to avoid rounding errors (e.g. `0.1 + 0.1 + 0.1 = 0.30000000000000004`).

## Part B1: Sentiment evaluation

The LLM predictions are given in the assignment and stored in
[`data/reviews.json`](data/reviews.json). No LLM is called. From the repository root:

```bash
python -m src.sentiment_evaluation
```

Output:

```text
Per-review results:
review_id reference_label predicted_label  correct
       R1           mixed        positive    False
       R2        positive        positive     True
       R3        negative        negative     True
       R4         neutral        positive    False

Total Reviews: 4
Correct Predictions: 2
Incorrect Predictions: 2
Accuracy: 50.00%

Misclassified Reviews:
review_id                                review_text reference_label predicted_label
       R1 Works fine but the battery died in a week.           mixed        positive
       R4                It's okay, nothing special.         neutral        positive
```

**Accuracy = correct predictions / total predictions = 2 / 4 = 50%.** Labels are compared
ignoring case and surrounding whitespace. A missing label counts as incorrect, and an empty
dataset raises an error instead of returning a misleading score.

Both errors are borderline reviews (mixed and neutral) that the LLM labelled positive. The
discussion of each case and the limits of this evaluation are in
[`docs/sentiment_error_analysis.md`](docs/sentiment_error_analysis.md).

## Future work

Remaining assignment requirements:

- **B2**: Model `Customer —purchased→ Product —belongsTo→ Category` as a knowledge graph.
- **B2**: Write a graph query that finds all products purchased by customers who left at
  least one negative review.
