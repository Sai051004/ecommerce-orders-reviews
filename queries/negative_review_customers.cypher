// Products purchased by customers who wrote at least one negative review.
// Equivalent to find_products_purchased_by_negative_reviewers() in src/knowledge_graph.py.
// Not executed against Neo4j: see docs/cypher_query_explanation.md.

MATCH (c:Customer)-[:wrote]->(r:Review)
WHERE r.reference_label = 'negative'
MATCH (c)-[:purchased]->(p:Product)
RETURN DISTINCT p.product_name AS product
ORDER BY product;
