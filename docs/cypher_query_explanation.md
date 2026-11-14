# Cypher Query Explanation (Part B2)

The assignment asks for a query that finds all products purchased by customers who left
at least one negative review. The project runs this query in Python with NetworkX
([`find_products_purchased_by_negative_reviewers`](../src/knowledge_graph.py)). This note
gives the equivalent query in Neo4j's Cypher language.

## The query

[`queries/negative_review_customers.cypher`](../queries/negative_review_customers.cypher):

```cypher
MATCH (c:Customer)-[:wrote]->(r:Review)
WHERE r.reference_label = 'negative'
MATCH (c)-[:purchased]->(p:Product)
RETURN DISTINCT p.product_name AS product
ORDER BY product;
```

It uses the same names as the NetworkX graph (see
[`knowledge_graph_design.md`](knowledge_graph_design.md)):

| NetworkX | Cypher |
|---|---|
| Node attribute `node_type="Customer"` / `"Review"` / `"Product"` | Node labels `:Customer`, `:Review`, `:Product` |
| Edge attribute `relationship="wrote"` / `"purchased"` | Relationship types `:wrote`, `:purchased` |
| Node attributes `reference_label`, `product_name` | Node properties `r.reference_label`, `p.product_name` |

## Clause by clause

### MATCH

```cypher
MATCH (c:Customer)-[:wrote]->(r:Review)
```

`MATCH` describes a pattern, and Cypher finds every part of the graph that fits it.
`(c:Customer)` is a node with the label `Customer`, bound to the variable `c`.
`-[:wrote]->` is a relationship of type `wrote` pointing from `c` to `r`, and `(r:Review)`
is a `Review` node. Each match produces one row with a `(c, r)` pair, so this finds every
customer–review pair where the customer wrote the review. The arrow matters: a `wrote`
relationship in the opposite direction would not match.

### WHERE

```cypher
WHERE r.reference_label = 'negative'
```

Keeps only the rows whose review has the reference (ground-truth) label `negative`. The
LLM's `predicted_label` is not used: Part B1 showed the predictions are wrong on 2 of the
4 reviews, so a business query should rely on the reference label. Labels like `mixed` or
`neutral` do not count as negative.

### Second MATCH

```cypher
MATCH (c)-[:purchased]->(p:Product)
```

`c` is already bound to the qualifying customers, so this pattern starts from them and
follows their outgoing `purchased` relationships to `Product` nodes. It finds **every**
product those customers bought, not just the product they reviewed: the review is only used
to decide which customers qualify. The `about` relationship is not part of the query.

Because this is a plain `MATCH`, a qualifying customer with no purchases produces no rows
and simply contributes nothing.

### DISTINCT

```cypher
RETURN DISTINCT p.product_name AS product
```

The matching can produce the same product more than once: a customer with two negative
reviews gives two rows for each of their purchases, and two qualifying customers may have
bought the same product. `DISTINCT` removes the duplicate rows so each product name appears
once. `AS product` names the output column.

### ORDER BY

```cypher
ORDER BY product;
```

Sorts the results by product name in ascending (alphabetical) order, matching the sorted
list returned by the NetworkX function.

## Expected result on the demo data

The customers and their links to orders and reviews in
[`data/graph_demo.json`](../data/graph_demo.json) are **synthetic**. The assignment data has
no customer identifiers, so they were invented to make the query demonstrable. Orders,
products, review IDs and review texts are the original assignment data.

| Review | Written by | Reference label |
|---|---|---|
| R1 | C2 | mixed |
| R2 | C1 | positive |
| R3 | C1 | **negative** |
| R4 | C3 | neutral |

| Customer | Orders | Products purchased |
|---|---|---|
| C1 | O3, O4, O5 | Yoga Mat, Desk Lamp, Yoga Mat |
| C2 | O1 | Wireless Mouse |
| C3 | O2 | Wireless Mouse |

1. `MATCH` + `WHERE` → the only row is `(C1, R3)`.
2. Second `MATCH` → `(C1, Yoga Mat)` and `(C1, Desk Lamp)`. C1 bought Yoga Mat twice (O3 and
   O5), but the graph has one `purchased` relationship per customer–product pair.
3. `DISTINCT` + `ORDER BY` → expected result:

| product |
|---|
| Desk Lamp |
| Yoga Mat |

Yoga Mat is included even though C1's review of it (R2) is positive, because C1 qualifies
through R3. Wireless Mouse is excluded because its buyers, C2 and C3, wrote no negative
review. This is the same result the NetworkX query prints.

## NetworkX vs Cypher

| Aspect | NetworkX | Neo4j Cypher |
|---|---|---|
| Execution | Python in-memory graph | Neo4j graph database |
| Query style | Procedural traversal | Declarative pattern matching |
| Graph storage | In memory | Database-managed |
| Best use | Small graphs and prototyping | Persistent graph applications |

Both implement the same logical query:

| Step | NetworkX (`src/knowledge_graph.py`) | Cypher |
|---|---|---|
| Find negative reviews | Loop over `graph.nodes(data=True)`, keep `Review` nodes with `reference_label == "negative"` | `(r:Review)` + `WHERE r.reference_label = 'negative'` |
| Find their authors | `graph.predecessors(review)`, keep `Customer` nodes with a `wrote` edge | `(c:Customer)-[:wrote]->(r)` |
| Find their purchases | `graph.successors(customer)`, keep `Product` nodes with a `purchased` edge | `MATCH (c)-[:purchased]->(p:Product)` |
| Remove duplicates | Collect names in a `set` | `DISTINCT` |
| Sort | `sorted(...)` | `ORDER BY product` |

In NetworkX the code spells out *how* to walk the graph. In Cypher the query describes
*what* pattern to find, and the database decides how to find it.

One small difference: the Python function compares the label ignoring case and surrounding
whitespace, while the Cypher `WHERE` is an exact match. The labels in this dataset are
already lowercase, so the results are the same. A case-insensitive Cypher version would be
`WHERE toLower(trim(r.reference_label)) = 'negative'`.

## Execution limitations

1. The Cypher query is provided as an **equivalent graph database query** for the
   assignment requirement.
2. The project executes its graph operations with **NetworkX**. No Neo4j database, driver
   or connection is part of the project.
3. The Cypher query **has not been executed against a Neo4j instance**.
4. It assumes the graph has been loaded into Neo4j with the same node labels (`Customer`,
   `Review`, `Product`), relationship types (`wrote`, `purchased`) and property names
   (`reference_label`, `product_name`) as the NetworkX graph.
5. Under that schema, the NetworkX and Cypher queries are **logically equivalent**, but the
   Cypher result has only been reasoned through by hand against the demo data, not verified
   by running it on a database.
