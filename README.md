# E-Commerce Orders & Reviews

My solution to the E-Commerce Orders & Reviews coding assignment for the Duck Creek
Technologies Associate Software Engineer (AI) role.

- Part A cleans the orders data and calculates revenue per category and the top 2 products
  by quantity.
- Part B1 scores the LLM sentiment labels against the reference labels and discusses the
  borderline reviews.
- Part B2 builds a Customer / Product / Category / Review graph and finds all products bought
  by customers who left at least one negative review.

Built with Python 3.11, pandas, scikit-learn (B1 metrics) and NetworkX (B2 graph).

## Project structure

```text
ecommerce-orders-reviews/
├── data/
│   ├── orders.json            # orders from the assignment
│   ├── reviews.json           # reviews and labels from the assignment
│   └── graph_demo.json        # made-up customer links for Part B2 (see below)
├── queries/
│   └── negative_review_customers.cypher
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py       # Part A
│   ├── sentiment_evaluation.py  # Part B1
│   └── knowledge_graph.py     # Part B2
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone https://github.com/Sai051004/ecommerce-orders-reviews.git
cd ecommerce-orders-reviews

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
```

I tested the code with the oldest and newest versions allowed in `requirements.txt`
(pandas 2.2.2 and 3.1.1, scikit-learn 1.4.2 and 1.9.1, NetworkX 3.2 and 3.6.1). Both gave
the same output.

## Running

Run from the repository root:

```bash
python -m src.data_cleaning          # Part A
python -m src.sentiment_evaluation   # Part B1
python -m src.knowledge_graph        # Part B2
```

Use `python -m` as shown. `knowledge_graph.py` imports the other two modules, so running it
as `python src/knowledge_graph.py` gives `ModuleNotFoundError: No module named 'src'`.

## Part A: Data cleaning

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

Revenue per category:

- Fitness: 5 x 15 + 2 x 15 = 105
- Electronics: 3 x 20 + 2 x 20 = 100
- Home: 1 x 25 = 25
- Total: 230

Top 2 by quantity: Yoga Mat (5 + 2 = 7) and Wireless Mouse (3 + 2 = 5). Desk Lamp is third
with 1.

### How the cleaning works

The raw data has three problems: `wireless mouse` vs `Wireless Mouse`, `electronics` vs
`Electronics`, and an empty category for order O3 (Yoga Mat).

1. `normalize_orders` trims product and category names, collapses repeated spaces, and
   capitalizes the first letter of each word, so `wireless mouse` becomes `Wireless Mouse`.
   Empty values become missing values instead of a placeholder like "Unknown".
2. `fill_missing_categories` looks at the orders that have a category and builds a
   product-to-category mapping. A missing category is only filled if that product has
   exactly one known category, so O3 gets `Fitness` from O5. If a product had two different
   categories, it would be left missing rather than guessed.
3. `calculate_category_revenue` multiplies `qty` by `unit_price` and sums per category,
   highest first. Orders whose category could not be filled are kept as a separate missing
   category so their revenue isn't lost.
4. `get_top_selling_products` sums `qty` per product and returns the top 2. Ties are sorted
   alphabetically.

The code also rejects bad input instead of silently giving wrong totals: duplicate order IDs,
and quantities or prices that are missing, non-numeric or negative, raise an error that
names the order.

## Part B1: Sentiment evaluation

The reviews and the LLM labels come from the assignment and are stored in
`data/reviews.json`. The code does not call an LLM; it only scores the labels it was given.

| ID | Review | Reference | LLM |
|---|---|---|---|
| R1 | "Works fine but the battery died in a week." | mixed | positive |
| R2 | "Exactly what I needed, five stars!" | positive | positive |
| R3 | "Arrived broken, waste of money." | negative | negative |
| R4 | "It's okay, nothing special." | neutral | positive |

Accuracy is 2 out of 4, or 50%. R2 and R3 are correct, and R1 and R4 are wrong.

I also calculated precision, recall and F1 per class:

```text
          precision  recall     f1  support
positive     0.3333  1.0000 0.5000        1
negative     1.0000  1.0000 1.0000        1
neutral      0.0000  0.0000 0.0000        1
mixed        0.0000  0.0000 0.0000        1

          precision  recall     f1
macro        0.3333  0.5000 0.3750
weighted     0.3333  0.5000 0.3750
```

Macro F1 is (0.5 + 1 + 0 + 0) / 4 = 0.375. The model never predicted neutral or mixed, so
their precision is 0/0, which is reported as 0.

Confusion matrix:

```text
predicted  positive  negative  neutral  mixed
actual
positive          1         0        0      0
negative          0         1        0      0
neutral           1         0        0      0
mixed             1         0        0      0
```

### Borderline cases

R1, "Works fine but the battery died in a week." (reference mixed, LLM positive): the review
starts positive but then reports a real failure. The LLM seems to have picked up "works fine"
and ignored the complaint. Mixed is a fair reference label, and some people would even call
it negative, since a battery dying within a week is a serious problem. Positive is the
weakest of the three.

R4, "It's okay, nothing special." (reference neutral, LLM positive): "okay" can sound mildly
positive, but "nothing special" pulls it back to average. I agree with neutral, but the
difference between neutral and slightly positive is subjective, so this one is genuinely
ambiguous.

R2 and R3 are clear, and the LLM got both right. Both mistakes went towards positive on
reviews that weren't clearly positive or negative. With only four reviews, though, that
isn't enough to say the model has a general bias.

## Part B2: Knowledge graph

The assignment data has no customers, so I made up a small mapping in
`data/graph_demo.json` to be able to run the query. It assigns the five orders to three
customers (C1, C2, C3) and says which customer wrote each review and which product it is
about. Only this mapping is invented. The orders, products, categories and reviews are the
original data.

| Customer | Orders | Reviews |
|---|---|---|
| C1 | O3 (Yoga Mat), O4 (Desk Lamp), O5 (Yoga Mat) | R2 about Yoga Mat, R3 about Desk Lamp |
| C2 | O1 (Wireless Mouse) | R1 about Wireless Mouse |
| C3 | O2 (Wireless Mouse) | R4 about Wireless Mouse |

The graph is a NetworkX `DiGraph` with four node types (Customer, Product, Category, Review)
and four edge types:

- Customer `purchased` Product
- Product `belongsTo` Category
- Customer `wrote` Review
- Review `about` Product

Products and categories come from the cleaned Part A data, so both spellings of Wireless Mouse
are one node. If a customer buys the same product twice, there is still only one
`purchased` edge.

`find_products_purchased_by_negative_reviewers` finds the reviews whose reference label is
negative, goes back along the `wrote` edges to the customers who wrote them, then returns
every product those customers purchased, without duplicates and sorted by name. It uses the
reference label, not the LLM's prediction.

Output:

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

R3 is the only negative review, and C1 wrote it. C1 bought Yoga Mat and Desk Lamp, so both
are returned, even though C1's review of the Yoga Mat (R2) was positive. Wireless Mouse is
not returned because C2 and C3 did not write any negative reviews.

### Cypher version

The same query in Cypher is in `queries/negative_review_customers.cypher`:

```cypher
MATCH (c:Customer)-[:wrote]->(r:Review)
WHERE r.reference_label = 'negative'
MATCH (c)-[:purchased]->(p:Product)
RETURN DISTINCT p.product_name AS product
ORDER BY product;
```

To check it, I loaded the same graph into a local Neo4j 5.26 Community server and ran the
query. It gave the same result as the NetworkX function on the assignment data and on a few
small test graphs:

| Graph | Cypher | NetworkX |
|---|---|---|
| Assignment data (13 nodes, 15 edges) | Desk Lamp, Yoga Mat | Desk Lamp, Yoga Mat |
| One negative review, two purchases | both products | both products |
| Several negative reviews by one customer | product once | product once |
| Two negative reviewers share a product | product once | product once |
| Customer with only a positive review | excluded | excluded |
| No negative reviews (mixed only) | empty | empty |
| Predicted negative, reference positive | empty | empty |
| Negative reviewer with no purchases | empty | empty |
| `wrote` edge in the reverse direction | empty | empty |

Neo4j isn't needed to run the project. One small difference: the Cypher `WHERE` needs the
label to be exactly `negative`, while the Python function also ignores case and extra
spaces. The labels in this data are already lowercase, so it makes no difference here.

## Assumptions and limitations

- A missing category is only filled when the product has one consistent category in the
  other orders.
- The capitalization rule is simple. It would change `iPhone` to `Iphone` and `Wi-Fi` to
  `Wi-fi`, which is fine for this data but not for brand names in general.
- Revenue uses floats. That's exact for these prices, but real financial code should use
  integer cents or `Decimal`.
- Four reviews is a very small sample, and sentiment labels are partly subjective, so the
  B1 numbers only describe these four reviews.
- The customer links in Part B2 are made up, and the query result depends on them.
- The graph is rebuilt in memory on every run. Because it keeps one edge per customer and
  product, it doesn't record how many times a customer bought something.
