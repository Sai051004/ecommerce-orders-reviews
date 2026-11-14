# Knowledge Graph Design (Part B2)

> Model as a graph: build a graph with edges like
> `Customer —purchased→ Product —belongsTo→ Category`. Write a query that finds all
> products purchased by customers who left at least one negative review.

This note defines the graph schema and the small demonstration dataset it is built from.
The graph itself and the query are implemented in a later step.

## Data sources

| Data | Source | Original or synthetic |
|---|---|---|
| Orders (order ID, product, category, qty, price) | [`data/orders.json`](../data/orders.json), cleaned by Part A | Original |
| Reviews (ID, text, reference and predicted labels) | [`data/reviews.json`](../data/reviews.json) | Original |
| Which customer placed each order | [`data/graph_demo.json`](../data/graph_demo.json) | **Synthetic** |
| Which customer wrote each review, and about which product | [`data/graph_demo.json`](../data/graph_demo.json) | **Synthetic** |

The assignment data has no customers and nothing linking reviews to orders or products,
so those links are invented for the demo. No orders, products or review texts are invented,
and the original files are not modified.

## Entities

### Customer

| Attribute | Example |
|---|---|
| `customer_id` | `C1` |

Customer IDs (`C1`, `C2`, `C3`) are synthetic.

### Product

| Attribute | Example |
|---|---|
| `product_id` | `P1` |
| `product_name` | `Wireless Mouse` |

One node per distinct product name after Part A cleaning:

| product_id | product_name |
|---|---|
| P1 | Wireless Mouse |
| P2 | Yoga Mat |
| P3 | Desk Lamp |

### Category

| Attribute | Example |
|---|---|
| `category_id` | `CAT1` |
| `category_name` | `Electronics` |

One node per distinct category after Part A cleaning:

| category_id | category_name |
|---|---|
| CAT1 | Electronics |
| CAT2 | Fitness |
| CAT3 | Home |

Product and category IDs are assigned in order of first appearance in the orders.

### Review

| Attribute | Example |
|---|---|
| `review_id` | `R3` |
| `review_text` | `Arrived broken, waste of money.` |
| `reference_label` | `negative` |
| `predicted_label` | `negative` |

The four reviews R1–R4 from `data/reviews.json` are used unchanged.

- `reference_label` is the ground-truth annotation supplied by the assignment.
- `predicted_label` is the LLM-generated prediction evaluated in Part B1.

The negative-review query uses **`reference_label == "negative"`**.

## Relationships

All relationships are directed.

| Relationship | From → To | Purpose | Source |
|---|---|---|---|
| `purchased` | Customer → Product | Records that a customer bought a product (one edge per customer–product pair, built from their orders) | Synthetic order → customer mapping + original orders |
| `belongsTo` | Product → Category | Places each product in its category | Original orders (Part A cleaned) |
| `wrote` | Customer → Review | Records who wrote each review | Synthetic |
| `about` | Review → Product | Records which product a review is about | Synthetic |

```text
Customer ──purchased──▶ Product ──belongsTo──▶ Category
    │                      ▲
    └──wrote──▶ Review ──about──┘
```

## Negative-review query

Logically, the query:

1. Finds reviews with `reference_label == "negative"`.
2. Follows `wrote` edges backwards to the customers who wrote them.
3. Follows those customers' `purchased` edges to every product they bought.
4. Returns the distinct products.

It returns **all** products purchased by a qualifying customer, not only the product they
reviewed negatively. The `about` edge is not needed for this query.
