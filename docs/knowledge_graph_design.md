# Knowledge Graph Design (Part B2)

> Model as a graph: build a graph with edges like
> `Customer —purchased→ Product —belongsTo→ Category`. Write a query that finds all
> products purchased by customers who left at least one negative review.

This note defines the graph schema and the small demonstration dataset it is built from.
The graph and the query are implemented in [`src/knowledge_graph.py`](../src/knowledge_graph.py).

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

## Synthetic demo dataset

[`data/graph_demo.json`](../data/graph_demo.json) holds the full mapping.

### Orders by customer

| Order | Customer | Product (cleaned) | Category (cleaned) | Qty |
|---|---|---|---|---:|
| O1 | C2 | Wireless Mouse | Electronics | 3 |
| O2 | C3 | Wireless Mouse | Electronics | 2 |
| O3 | C1 | Yoga Mat | Fitness | 5 |
| O4 | C1 | Desk Lamp | Home | 1 |
| O5 | C1 | Yoga Mat | Fitness | 2 |

### Reviews by customer

| Review | Customer | About | Reference label | Text |
|---|---|---|---|---|
| R1 | C2 | Wireless Mouse | mixed | "Works fine but the battery died in a week." |
| R2 | C1 | Yoga Mat | positive | "Exactly what I needed, five stars!" |
| R3 | C1 | Desk Lamp | **negative** | "Arrived broken, waste of money." |
| R4 | C3 | Wireless Mouse | neutral | "It's okay, nothing special." |

Every review is about a product its author actually purchased.

### Resulting edges

| Edge type | Edges |
|---|---|
| `purchased` | C1 → Yoga Mat, C1 → Desk Lamp, C2 → Wireless Mouse, C3 → Wireless Mouse |
| `belongsTo` | Wireless Mouse → Electronics, Yoga Mat → Fitness, Desk Lamp → Home |
| `wrote` | C1 → R2, C1 → R3, C2 → R1, C3 → R4 |
| `about` | R1 → Wireless Mouse, R2 → Yoga Mat, R3 → Desk Lamp, R4 → Wireless Mouse |

C1 bought Yoga Mat twice (O3 and O5). That is one `purchased` edge, not two.

## Expected query result

1. Negative reviews: **R3** only.
2. Customer who wrote R3: **C1**.
3. Products C1 purchased: Yoga Mat (O3), Desk Lamp (O4), Yoga Mat (O5).
4. Distinct products: **Desk Lamp, Yoga Mat**.

| Product | Why it is returned |
|---|---|
| Desk Lamp | Purchased by C1, who reviewed it negatively (R3) |
| Yoga Mat | Purchased by C1. C1 reviewed it *positively* (R2), but C1 qualifies because of R3 |

Wireless Mouse is **not** returned: its buyers, C2 and C3, wrote only mixed (R1) and
neutral (R4) reviews. *Mixed* is not *negative*, so R1 does not qualify.

The demo is built to exercise these cases:

- A qualifying customer bought more than one distinct product, so the query must return
  products beyond the one reviewed negatively.
- The same product was bought twice by one customer, so duplicates must be removed.
- A qualifying customer also wrote a positive review, so the rule is "at least one
  negative review", not "only negative reviews".

Using `predicted_label` instead would give the same result here (R3 is the only review
predicted negative), but the query is defined on `reference_label`.

## Modeling decisions

1. **Separate entities.** Customers, products, categories and reviews are different kinds
   of things with different attributes. As separate nodes, each fact is stored once and can
   be shared: one Category node serves every product in it, and one Product node connects
   all its buyers and reviews.
2. **Directed relationships.** `purchased`, `belongsTo`, `wrote` and `about` all have a
   natural direction (a customer buys a product, not the reverse). Direction makes the
   meaning unambiguous and tells the query which way to traverse.
3. **Synthetic customer IDs.** The assignment data has no customers or links between orders,
   reviews and products. A small invented mapping is the minimum needed to demonstrate the
   query. It is labelled `synthetic_demo` so it is never mistaken for assignment data.
4. **Product IDs, not names, as node identifiers.** Names are display text: they can be
   misspelled, re-cased (`wireless mouse` vs `Wireless Mouse`), renamed, or shared by two
   different products. A stable ID keeps the node's identity independent of its label.
   Here the IDs are assigned from Part A's cleaned names, so the raw casing variants map to
   one product.
5. **Reference labels for the query.** `reference_label` is the ground truth. Part B1 shows
   the LLM predictions are wrong half the time on this sample, so a business query should not
   depend on them. Predictions stay on the Review node for comparison.
6. **Many orders, one product node.** O1 and O2 are both Wireless Mouse after cleaning, and
   O3 and O5 are both Yoga Mat. Each product is a single node, and every order of it points
   to that node.
7. **No duplicate results.** A customer who buys the same product several times gets one
   `purchased` edge per product (order details such as quantity could be stored as edge
   attributes if needed). The query returns a set of products, so even if two qualifying
   customers bought the same product, it appears once.
8. **Unresolved categories.** If Part A could not infer a product's category, the Product
   node is kept but gets **no** `belongsTo` edge. No placeholder category such as
   `"Unknown"` is created. In this dataset every product has a category, since O3's
   missing category is filled from O5.
9. **Typed nodes even if IDs overlap.** Each node carries a `node_type` (Customer, Product,
   Category, Review), and node keys are prefixed with the type (e.g. `product:P1`). That way
   two entities that happen to share an ID string never merge into one node, and queries
   can filter by type (e.g. "Review nodes with a negative label").
