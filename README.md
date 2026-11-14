# E-Commerce Orders & Reviews — Duck Creek Assignment

Coding assignment for the Duck Creek Technologies Associate Software Engineer (AI) role.

## Project overview

The project implements three components:

1. **Order data cleaning and aggregation (Part A).** Cleans a messy orders dataset
   (inconsistent casing, a missing category), then computes total revenue per category and
   the top 2 best-selling products by quantity.
2. **LLM sentiment classification evaluation (Part B1).** Scores LLM-generated sentiment
   labels against reference labels and discusses the ambiguous cases.
3. **Knowledge graph modeling and querying (Part B2).** Builds a
   `Customer —purchased→ Product —belongsTo→ Category` graph and finds all products
   purchased by customers who left at least one negative review.

## Tech stack

- **Python 3.11**
- **pandas**: loading, cleaning and aggregating the data
- **scikit-learn**: precision, recall, F1 and confusion matrix (Part B1)
- **NetworkX**: the in-memory knowledge graph and its query (Part B2)

A Cypher version of the graph query is included as a text file only. No Neo4j database,
driver or LLM API is used.

## Project structure

```text
ecommerce-orders-reviews/
├── data/
│   ├── orders.json                  # Part A input: the five original orders (unmodified)
│   ├── reviews.json                 # Part B1 input: the four original reviews (unmodified)
│   └── graph_demo.json              # Part B2: SYNTHETIC customer / review links for the demo
├── docs/
│   ├── sentiment_error_analysis.md  # Part B1: misclassified and borderline reviews
│   ├── knowledge_graph_design.md    # Part B2: graph schema, demo data, modeling decisions
│   └── cypher_query_explanation.md  # Part B2: equivalent Cypher query, clause by clause
├── queries/
│   └── negative_review_customers.cypher  # Part B2: equivalent Neo4j Cypher query
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py             # Part A: load, clean, revenue, top sellers
│   ├── sentiment_evaluation.py      # Part B1: accuracy, errors, metrics, confusion matrix
│   └── knowledge_graph.py           # Part B2: build the graph and run the query
├── .gitignore
└── README.md
```

## Installation

Developed and verified with Python 3.11 (pandas 3.1, scikit-learn 1.9, NetworkX 3.6).
Dependencies are installed directly with pip. No configuration, environment variables or
API keys are needed.

```bash
git clone https://github.com/Sai051004/ecommerce-orders-reviews.git
cd ecommerce-orders-reviews

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install pandas scikit-learn networkx
```

## Running the project

Run each part from the repository root, as a module (`python -m`):

```bash
python -m src.data_cleaning          # Part A
python -m src.sentiment_evaluation   # Part B1
python -m src.knowledge_graph        # Part B2
```

`src.knowledge_graph` imports the Part A and B1 loaders, so it must be run with `-m` from
the root (`python src/knowledge_graph.py` fails with `ModuleNotFoundError: No module named 'src'`).

## Part A — Order cleaning and aggregation

### Results

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

| Category | Calculation | Total revenue |
|---|---|---:|
| Fitness | O3 (5 × 15.00) + O5 (2 × 15.00) | 105.00 |
| Electronics | O1 (3 × 20.00) + O2 (2 × 20.00) | 100.00 |
| Home | O4 (1 × 25.00) | 25.00 |
| **Total** | | **230.00** |

| Rank | Product | Calculation | Quantity |
|---:|---|---|---:|
| 1 | Yoga Mat | O3 (5) + O5 (2) | 7 |
| 2 | Wireless Mouse | O1 (3) + O2 (2) | 5 |

### Cleaning approach

All functions are in [`src/data_cleaning.py`](src/data_cleaning.py) and return new
DataFrames without modifying their input:

```text
load_orders → normalize_orders → fill_missing_categories ─┬→ calculate_category_revenue
                                                          └→ get_top_selling_products
```

The raw data has three problems:

| Issue | Example |
|---|---|
| Inconsistent product casing | `Wireless Mouse` (O1) vs `wireless mouse` (O2) |
| Inconsistent category casing | `electronics` (O1) vs `Electronics` (O2) |
| Missing category | O3 `Yoga Mat` has category `""` |

**Normalization** (`normalize_orders`): product and category values are whitespace-collapsed,
trimmed, lower-cased and then the first letter of each word is capitalized
(`"wireless mouse"` → `"Wireless Mouse"`, `"men's shoes"` → `"Men's Shoes"`). Empty values
become a true missing value (`pd.NA`), never a placeholder like `"Unknown"`. A duplicated
`order_id` raises an error, since it would be counted twice.

**Category inference** (`fill_missing_categories`): a product → category mapping is learned
from orders where both are known, using only products with **exactly one** known category.
Only missing categories are filled. O3 `Yoga Mat` gets `Fitness` from O5.

| Situation | Result |
|---|---|
| Product has one known category | Missing category is filled |
| Product has conflicting categories | Left missing, not guessed |
| Product has no known category | Left missing |

**Revenue**: `qty × unit_price` per order, summed per category, highest first. Orders whose
category cannot be resolved stay in the result as an `<NA>` row, so no revenue is dropped.
A missing, non-numeric or negative `qty` or `unit_price` raises an error naming the order,
instead of being silently treated as 0. Numeric strings such as `"3"` are converted.

**Top sellers**: total `qty` per normalized product name, highest first, ties broken
alphabetically. Orders with no product name are excluded. `qty` is validated the same way as
for revenue, and `top_n` must be a positive integer.

## Part B1 — LLM sentiment evaluation

The four reviews and their LLM predictions are supplied by the assignment in
[`data/reviews.json`](data/reviews.json). **No live LLM is called.**

| Review | Text | Reference | LLM prediction | Correct |
|---|---|---|---|---|
| R1 | "Works fine but the battery died in a week." | mixed | positive | No |
| R2 | "Exactly what I needed, five stars!" | positive | positive | Yes |
| R3 | "Arrived broken, waste of money." | negative | negative | Yes |
| R4 | "It's okay, nothing special." | neutral | positive | No |

### Results

**4 reviews, 2 correct, 2 incorrect. Accuracy: 50%. Macro F1: 0.3750.**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| positive | 0.3333 | 1.0000 | 0.5000 | 1 |
| negative | 1.0000 | 1.0000 | 1.0000 | 1 |
| neutral | 0.0000 | 0.0000 | 0.0000 | 1 |
| mixed | 0.0000 | 0.0000 | 0.0000 | 1 |
| **macro avg** | 0.3333 | 0.5000 | 0.3750 | |
| **weighted avg** | 0.3333 | 0.5000 | 0.3750 | |

Macro F1 = (0.5 + 1.0 + 0 + 0) / 4 = 0.375. (Macro *precision* is 0.3333.) Precision for a
class that is never predicted is 0 / 0 and is reported as 0 (`zero_division=0`).

| Actual \ Predicted | positive | negative | neutral | mixed |
|---|---:|---:|---:|---:|
| **positive** | 1 | 0 | 0 | 0 |
| **negative** | 0 | 1 | 0 | 0 |
| **neutral** | 1 | 0 | 0 | 0 |
| **mixed** | 1 | 0 | 0 | 0 |

### Error analysis

- **R1** (*mixed* → *positive*): the review has a positive part ("works fine") and a
  negative part ("battery died in a week"). The prediction misses the complaint. Under some
  annotation guidelines it could even be *negative*.
- **R4** (*neutral* → *positive*): "okay" is not necessarily positive, and "nothing special"
  points to an average experience. The line between *neutral* and *mildly positive* is
  subjective.

The two clear-cut reviews (R2, R3) were classified correctly. Both errors are borderline
reviews predicted as *positive*, and the model never predicted *mixed* or *neutral*. Four
reviews are not enough to conclude that the model is biased in general. Full discussion:
[`docs/sentiment_error_analysis.md`](docs/sentiment_error_analysis.md).

The code is in [`src/sentiment_evaluation.py`](src/sentiment_evaluation.py). Labels are
compared ignoring case and whitespace. A missing label, or a label outside the four classes,
raises an error in both the accuracy and the metrics instead of being silently miscounted.

## Part B2 — Knowledge graph

> **Synthetic data.** The assignment data has no customers and nothing linking orders and
> reviews to customers or products. The customer IDs (`C1`–`C3`), the order → customer
> assignments and the review → customer/product links in
> [`data/graph_demo.json`](data/graph_demo.json) were **invented to demonstrate the query**.
> They are not facts from the assignment. Orders, products, categories and reviews are the
> original data.

### Schema

| Node type | Attributes | Nodes in the demo graph |
|---|---|---|
| Customer | `customer_id` | C1, C2, C3 (synthetic) |
| Product | `product_id`, `product_name` | P1 Wireless Mouse, P2 Yoga Mat, P3 Desk Lamp |
| Category | `category_id`, `category_name` | CAT1 Electronics, CAT2 Fitness, CAT3 Home |
| Review | `review_id`, `review_text`, `reference_label`, `predicted_label` | R1–R4 |

| Relationship | Direction | Built from |
|---|---|---|
| `purchased` | Customer → Product | Synthetic order → customer mapping + cleaned orders |
| `belongsTo` | Product → Category | Cleaned orders (only when a product has one category) |
| `wrote` | Customer → Review | Synthetic mapping |
| `about` | Review → Product | Synthetic mapping |

### Implementation

[`src/knowledge_graph.py`](src/knowledge_graph.py):

- `build_knowledge_graph(orders_df, reviews_df, graph_data)` builds an `nx.DiGraph` from the
  Part A cleaned orders, the Part B1 reviews and the synthetic mapping. Node keys are
  prefixed by type (`customer:C1`, `product:P1`) so different entity types never collide.
  Repeat purchases of a product by one customer become one `purchased` edge. References to
  unknown orders, reviews or products, blank customer IDs, or an order or review listed
  twice in the mapping raise a `ValueError`.
- `find_products_purchased_by_negative_reviewers(graph)`:
  1. finds Review nodes with `reference_label == "negative"` (the ground truth, not the LLM
     prediction);
  2. follows incoming `wrote` edges to their Customer authors;
  3. follows those customers' outgoing `purchased` edges to Product nodes;
  4. returns the distinct product names, sorted.

  It returns **all** products those customers bought, not just the reviewed product.

### Output

```text
Knowledge Graph Summary
-----------------------
Total Nodes: 13
Total Edges: 15

Node Types:
Customer: 3
Product: 3
Category: 3
Review: 4

Relationship Types:
purchased: 4
belongsTo: 3
wrote: 4
about: 4

Products Purchased by Customers with Negative Reviews:
- Desk Lamp
- Yoga Mat
```

Only R3 ("Arrived broken, waste of money.") is negative, and in the synthetic mapping it was
written by C1. C1 bought Yoga Mat (O3, O5) and Desk Lamp (O4), so both are returned, even
though C1's own review of Yoga Mat (R2) is positive. Wireless Mouse is not returned because
its buyers (C2, C3) wrote only mixed and neutral reviews. Design details:
[`docs/knowledge_graph_design.md`](docs/knowledge_graph_design.md).

### Optional Cypher query

[`queries/negative_review_customers.cypher`](queries/negative_review_customers.cypher)
contains the equivalent Neo4j query:

```cypher
MATCH (c:Customer)-[:wrote]->(r:Review)
WHERE r.reference_label = 'negative'
MATCH (c)-[:purchased]->(p:Product)
RETURN DISTINCT p.product_name AS product
ORDER BY product;
```

It is documented for comparison but **has not been executed against a Neo4j instance**. It
assumes the graph was loaded into Neo4j with the same labels, relationship types and
property names. Explanation: [`docs/cypher_query_explanation.md`](docs/cypher_query_explanation.md).

## Assumptions and limitations

- **Category inference relies on consistent product-category mappings.** A missing category
  is filled only when the product has exactly one known category. Conflicts are left
  missing for manual review.
- **Capitalization is a simple rule.** It would turn `iPhone` into `Iphone` and `Wi-Fi` into
  `Wi-fi`, which is fine for this dataset but not for brand names in general.
- **Revenue uses floats.** Exact for these prices, but production code should use integer
  cents or `decimal.Decimal`.
- **Only four sentiment examples are available.** Each review moves accuracy by 25
  percentage points, so the metrics describe these reviews, not general model performance.
- **Sentiment labels are subjective.** The references for R1 and R4 are reasonable but
  debatable.
- **The original dataset lacks customer identifiers.** Synthetic relationships are necessary
  to demonstrate the graph query, and the query result depends on them.
- **The graph is an in-memory demonstration**, rebuilt on every run, not a production graph
  database. A `DiGraph` keeps one edge per customer–product pair, so per-order details
  (e.g. C1's two Yoga Mat orders) are not stored on the graph.

## Future improvements

Not implemented. Possible next steps:

- A larger, representative labelled dataset for the sentiment evaluation.
- Automated regression checks for the three parts.
- Loading the graph into a graph database such as Neo4j and running the Cypher query there.
- Fuzzy matching of near-duplicate product names (e.g. `Wireless-Mouse` vs `Wireless Mouse`).
