# E-Commerce Orders & Reviews

Coding assignment for the Duck Creek Technologies Associate Software Engineer (AI) role.

**Part A** is a Python and pandas data-processing pipeline that:

- Loads raw e-commerce orders from JSON.
- Normalizes inconsistent product and category names.
- Infers missing categories from existing records.
- Calculates total revenue by category.
- Identifies the top 2 best-selling products by quantity.

**Part B1** evaluates LLM-generated sentiment labels against reference labels. See
[Part B1 — LLM Sentiment Evaluation](#part-b1--llm-sentiment-evaluation).

**Part B2** (knowledge graph) is not yet implemented. See [Remaining work](#remaining-work).

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
│   └── sentiment_evaluation.py  # Part B1: accuracy, error analysis, precision/recall/F1, confusion matrix
├── .gitignore
└── README.md
```

## Installation and setup

Requires Python 3, pandas, scikit-learn and NetworkX (developed with Python 3.11, pandas 3.1,
scikit-learn 1.9 and NetworkX 3.6). scikit-learn is only used by the Part B1 metrics, and
NetworkX only by the Part B2 knowledge graph.

```bash
git clone https://github.com/Sai051004/ecommerce-orders-reviews.git
cd ecommerce-orders-reviews

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install pandas scikit-learn networkx
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

## Part B1 — LLM Sentiment Evaluation

### Problem statement

The assignment provides four customer reviews, each with a reference sentiment label and
an LLM-generated prediction. The goal is to score the predictions against the references
and discuss the ambiguous or borderline cases.

### Evaluation dataset

The four reviews are stored exactly as given in [`data/reviews.json`](data/reviews.json).

| Review ID | Review | Reference | LLM prediction |
|---|---|---|---|
| R1 | "Works fine but the battery died in a week." | mixed | positive |
| R2 | "Exactly what I needed, five stars!" | positive | positive |
| R3 | "Arrived broken, waste of money." | negative | negative |
| R4 | "It's okay, nothing special." | neutral | positive |

The predictions are supplied by the assignment. No live LLM API is called.

### Evaluation methodology

All logic is in [`src/sentiment_evaluation.py`](src/sentiment_evaluation.py):

1. **Load** the reviews from JSON into a pandas DataFrame.
2. **Compare** reference and predicted labels row by row, ignoring case and surrounding
   whitespace. A missing label counts as incorrect.
3. **Accuracy** = correct predictions / total predictions. Empty input raises an error.
4. **Error analysis** returns only the misclassified reviews with their text and labels.
5. **Per-class precision, recall and F1** (scikit-learn) for the four classes in a fixed
   order: positive, negative, neutral, mixed. Labels outside these four raise an error
   instead of being silently dropped.
6. **Macro average** (each class weighted equally) and **weighted average** (each class
   weighted by its number of examples).
7. **Confusion matrix** with actual labels as rows and predicted labels as columns, always
   including all four classes.

### Evaluation results

**Accuracy: 50% (2 of 4 correct). Macro F1: 0.3750.**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| positive | 0.3333 | 1.0000 | 0.5000 | 1 |
| negative | 1.0000 | 1.0000 | 1.0000 | 1 |
| neutral | 0.0000 | 0.0000 | 0.0000 | 1 |
| mixed | 0.0000 | 0.0000 | 0.0000 | 1 |
| **macro avg** | 0.3333 | 0.5000 | 0.3750 | |
| **weighted avg** | 0.3333 | 0.5000 | 0.3750 | |

Macro F1 is the mean of the per-class F1 scores: (0.5 + 1.0 + 0 + 0) / 4 = 0.375. The
weighted average equals the macro average because every class has exactly one example.

Confusion matrix (rows = actual, columns = predicted):

| Actual \ Predicted | positive | negative | neutral | mixed |
|---|---:|---:|---:|---:|
| **positive** | 1 | 0 | 0 | 0 |
| **negative** | 0 | 1 | 0 | 0 |
| **neutral** | 1 | 0 | 0 | 0 |
| **mixed** | 1 | 0 | 0 | 0 |

R2 and R3 are on the diagonal (correct). R4 (neutral) and R1 (mixed) were both predicted
positive, and the neutral and mixed columns are empty.

### Error analysis

**R1: "Works fine but the battery died in a week."**: reference *mixed*, predicted *positive*.
The review contains both positive ("works fine") and negative ("battery died in a week")
sentiment. The prediction reflects the positive phrase and misses the complaint. The battery
failure makes the review *mixed*, or even *negative* under some annotation guidelines.

**R4: "It's okay, nothing special."**: reference *neutral*, predicted *positive*.
"Okay" does not necessarily mean positive, and "nothing special" suggests an average or
underwhelming experience. The line between *neutral* and *mildly positive* is subjective.

The two clear-cut reviews (R2 positive, R3 negative) were classified correctly. A fuller
discussion is in [`docs/sentiment_error_analysis.md`](docs/sentiment_error_analysis.md).

### Evaluation limitations

- **Only four reviews.** Each review moves accuracy by 25 percentage points, and every
  per-class score can only be 0, 0.5 or 1.
- **Too small for reliable estimates.** These results describe these four reviews, not how
  the model would perform on new data. They are not enough to conclude that the model is
  generally biased in any direction.
- **Sentiment labels are subjective.** The reference labels for R1 and R4 are reasonable
  but debatable, so the references are not automatically correct.
- **The model never predicts `mixed` or `neutral`** in this sample, so those classes
  have zero recall.
- **Undefined metrics.** Precision for a class that is never predicted is 0 / 0. It is
  reported as 0 using `zero_division=0`.
- **For production evaluation**, a larger, representative labelled dataset covering all
  four classes is needed, with clear annotation guidelines (e.g. when a complaint turns
  *mixed* into *negative*) and ideally several annotators per review.

### Running Part B1

From the repository root:

```bash
python -m src.sentiment_evaluation
```

This prints the per-review results, accuracy, misclassified reviews, per-class and averaged
metrics, and the confusion matrix.

## Remaining work

**Part B2: Knowledge graph modeling** (not yet implemented):

- Model `Customer`, `Product`, `Category` and `Review` entities and their relationships
  (e.g. `Customer —purchased→ Product —belongsTo→ Category`).
- Implement graph traversal and querying.
- Find all products purchased by customers who left at least one negative review.
