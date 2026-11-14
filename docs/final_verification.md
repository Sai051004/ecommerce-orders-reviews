# Final Verification Report

This report checks the submission against the assignment requirements. All results below
were produced by running the code. Nothing was copied from expected values.

**Environment:** Python 3.11.16, pandas 3.1.1, scikit-learn 1.9.1, NetworkX 3.6.1, Windows 11.
The commands were run both in the project's virtual environment and in a fresh virtual
environment built from only the tracked files plus `pip install pandas scikit-learn networkx`.
Both gave identical output.

## 1. Requirement checklist

| # | Requirement (from the assignment) | Implemented in | Status |
|---|---|---|---|
| A1 | Clean the orders data: inconsistent casing, missing category | `src/data_cleaning.py` (`normalize_orders`, `fill_missing_categories`) | ✅ Pass |
| A2 | Total revenue per category | `src/data_cleaning.py` (`calculate_category_revenue`) | ✅ Pass |
| A3 | Top 2 best-selling products by quantity | `src/data_cleaning.py` (`get_top_selling_products`) | ✅ Pass |
| B1a | Evaluate the LLM sentiment labels against the reference labels | `src/sentiment_evaluation.py` | ✅ Pass |
| B1b | Score accuracy | `src/sentiment_evaluation.py` (`calculate_accuracy`) | ✅ Pass |
| B1c | Discuss ambiguous cases | `docs/sentiment_error_analysis.md`, README | ✅ Pass |
| B2a | Build a graph `Customer —purchased→ Product —belongsTo→ Category` | `src/knowledge_graph.py` (`build_knowledge_graph`), `docs/knowledge_graph_design.md` | ✅ Pass (with synthetic customer data, see §6) |
| B2b | Query: products purchased by customers with at least one negative review | `src/knowledge_graph.py` (`find_products_purchased_by_negative_reviewers`) | ✅ Pass |
| B2c | Equivalent Cypher query (optional extra) | `queries/negative_review_customers.cypher`, `docs/cypher_query_explanation.md` | ⚠️ Documented only, **not executed** on Neo4j |
| B3 | Share the GitHub link | https://github.com/Sai051004/ecommerce-orders-reviews | ✅ Pass (public, HTTP 200) |

Extras beyond the assignment: per-class precision / recall / F1, macro and weighted
averages, and a confusion matrix for B1.

## 2. Commands executed

From the repository root:

```bash
python -m src.data_cleaning          # Part A
python -m src.sentiment_evaluation   # Part B1
python -m src.knowledge_graph        # Part B2
```

All three exit successfully, and two consecutive runs of each give byte-identical output.
`python src/knowledge_graph.py` (without `-m`) fails with
`ModuleNotFoundError: No module named 'src'`. The README says to use `-m`.

## 3. Actual results

### Part A

Output excerpt:

```text
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

| Check | Result | Status |
|---|---|---|
| Five original orders loaded | 5 | ✅ |
| Product names normalized | 4 raw spellings → 3 products (`wireless mouse` → `Wireless Mouse`) | ✅ |
| Category names normalized | `electronics` → `Electronics`; categories are Electronics, Fitness, Home | ✅ |
| Missing O3 Yoga Mat category inferred | `Fitness` (from O5) | ✅ |
| Revenue per category | Fitness 105.00, Electronics 100.00, Home 25.00 | ✅ |
| Total revenue | 230.00 | ✅ |
| Top 2 by quantity | Yoga Mat 7, Wireless Mouse 5 | ✅ |

### Part B1

Output excerpt (per-class metrics and confusion matrix are in the README):

```text
Total Reviews: 4
Correct Predictions: 2
Incorrect Predictions: 2
Accuracy: 50.00%

Misclassified Reviews:
review_id                                review_text reference_label predicted_label
       R1 Works fine but the battery died in a week.           mixed        positive
       R4                It's okay, nothing special.         neutral        positive

Averaged Metrics:
          precision  recall     f1
macro        0.3333  0.5000 0.3750
weighted     0.3333  0.5000 0.3750
```

| Check | Result | Status |
|---|---|---|
| Four reviews loaded | 4 | ✅ |
| Accuracy | 0.5 | ✅ |
| Misclassified reviews | R1, R4 | ✅ |
| Macro F1 | **0.3750** = (0.5 + 1 + 0 + 0) / 4 | ✅ (see note) |
| Confusion matrix | 4 observations, 2 on the diagonal | ✅ |
| Deterministic | Identical output on repeated runs | ✅ |

**Note:** an earlier expectation of macro F1 ≈ 0.3333 was incorrect. 0.3333 is the macro
*precision*. Macro F1, both from scikit-learn and by hand, is 0.375.

The predictions are supplied by the assignment. No live LLM is called.

### Part B2

Output excerpt (the full output is in the README):

```text
Total Nodes: 13
Total Edges: 15

Products Purchased by Customers with Negative Reviews:
- Desk Lamp
- Yoga Mat
```

| Check | Result | Status |
|---|---|---|
| All node types present | Customer, Product, Category, Review | ✅ |
| All relationship types present | purchased, belongsTo, wrote, about | ✅ |
| Products come from cleaned data | Wireless Mouse, Yoga Mat, Desk Lamp (no casing duplicates) | ✅ |
| Customers come from the synthetic mapping | C1, C2, C3 from `data/graph_demo.json` | ✅ |
| Query result | Desk Lamp, Yoga Mat | ✅ |
| Matches the synthetic data by hand | Only R3 is negative → written by C1 → C1 bought O3 Yoga Mat, O4 Desk Lamp, O5 Yoga Mat | ✅ |
| Sorted and deterministic | Same sorted list on repeated runs | ✅ |
| Cypher query executed on Neo4j | Not executed | ⚠️ Not verified |

## 4. Edge-case review

| Area | Case | Behaviour | Status |
|---|---|---|---|
| A | Empty / whitespace category | Becomes a true missing value, then filled if unambiguous | ✅ |
| A | Product casing / extra spaces | `" yoga  MAT "` → `Yoga Mat` | ✅ |
| A | Conflicting product categories | Missing category left missing, not guessed | ✅ |
| A | Duplicate names after normalization | Grouped as one product | ✅ |
| A | Ties in top sellers | Broken alphabetically (deterministic) | ✅ |
| A | Unresolved category in revenue | Kept as an `<NA>` row, not dropped | ✅ |
| B1 | Incorrect predictions | Listed by `analyze_errors` | ✅ |
| B1 | Classes never predicted (neutral, mixed) | Precision 0 via `zero_division=0`, no crash | ✅ |
| B1 | Labels with different case / spaces | Compared case- and whitespace-insensitively | ✅ |
| B1 | Unsupported label in metrics | Raises `ValueError` (not silently dropped) | ✅ |
| B2 | Same product bought twice (C1: O3, O5) | One `purchased` edge, one result | ✅ |
| B2 | Several negative reviews by one customer | Customer counted once, no duplicate products | ✅ |
| B2 | No negative reviews | Returns `[]`, prints a "None" message | ✅ |
| B2 | Unknown order / review / product, blank customer ID, order given to two customers | Raises `ValueError` | ✅ |
| B2 | Relationship direction and type | Only incoming `wrote` from Customers and outgoing `purchased` to Products count | ✅ |
| B2 | Reference vs predicted label | Only `reference_label` is used | ✅ |

### Gaps found (not fixed)

None of these affects the assignment data or its results. They are listed for completeness.

1. **Part A: missing `qty` or `unit_price` is silently ignored in revenue.** pandas `sum()`
   skips missing values, so an order with no quantity contributes 0 without a warning.
2. **Part B1: accuracy and metrics treat unsupported labels differently.** For example
   `"very positive"` counts as incorrect in `calculate_accuracy`, but makes
   `calculate_classification_metrics` raise `ValueError`.
3. **Part B2: one review can be linked to two customers.** `order_customers` rejects an order
   assigned twice, but `review_relationships` accepts a review listed twice. That would add
   two `wrote` edges into the same review.

A review about a product its author never bought is also accepted. That is allowed by
design, since the query does not use the `about` edge.

## 5. Repository hygiene

| Check | Result | Status |
|---|---|---|
| Dependencies declared | pandas, scikit-learn, NetworkX in the README install command; all three are imported by the code | ✅ |
| No unnecessary dependencies | No other third-party imports | ✅ |
| Virtual environment ignored | `.venv/` in `.gitignore` | ✅ |
| Python caches ignored | `__pycache__/`, `*.pyc`, `.pytest_cache/` in `.gitignore` | ✅ |
| No secrets / API keys tracked | None found in tracked files | ✅ |
| No temporary output files tracked | Only source, data, docs and the query are tracked | ✅ |
| No hardcoded results in code | Outputs are computed; no result values in `src/` | ✅ |
| Original datasets unchanged | SHA-256 of `orders.json` and `reviews.json` unchanged | ✅ |
| README commands work | Verified in a fresh virtual environment | ✅ |
| README output blocks match real output | Part A and Part B2 blocks and B1 tables checked programmatically | ✅ |
| All documentation links resolve | Checked programmatically | ✅ |

## 6. Remaining limitations

- **Synthetic customer data.** The assignment has no customer identifiers. Customers
  C1–C3, the order → customer assignments and the review → customer/product links in
  `data/graph_demo.json` are invented to demonstrate the graph query. The query result
  (Desk Lamp, Yoga Mat) depends on that mapping.
- **Cypher not executed.** The Cypher query is equivalent by design but has not been run
  against a Neo4j database.
- **Tiny sentiment sample.** Four reviews, so each review moves accuracy by 25 points. The
  metrics describe this sample, not general model performance.
- **Subjective labels.** The reference labels for R1 and R4 are reasonable but debatable.
- **In-memory graph.** NetworkX `DiGraph`, rebuilt on every run. It keeps one edge per
  customer–product pair, so per-order details are not stored.
- **Simple normalization.** Title case would mis-handle brand names such as `iPhone`.
- **No automated test suite in the repository.** Verification was done with assertion
  scripts and by running the entry points.

## 7. Conclusion

Every assignment requirement (A1–A3, B1, B2, B3) is implemented and verified. The results
are reproducible from a fresh install, and the documentation matches the code. The only
unverified item is the optional Cypher query, which is clearly marked as not executed. The
three validation gaps in §4 do not affect the assignment results.

**The repository is ready for submission.**
