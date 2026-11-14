"""Build a Customer / Product / Category / Review knowledge graph with NetworkX.

The schema is described in docs/knowledge_graph_design.md. Orders and reviews come
from the assignment data. Customers and their links to orders and reviews come from
the synthetic demo mapping in data/graph_demo.json.
"""

import json
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd

from src.data_cleaning import fill_missing_categories, load_orders, normalize_orders
from src.sentiment_evaluation import load_reviews

NODE_TYPES = ["Customer", "Product", "Category", "Review"]
RELATIONSHIPS = ["purchased", "belongsTo", "wrote", "about"]


def customer_node(customer_id: str) -> str:
    return f"customer:{customer_id}"


def product_node(product_id: str) -> str:
    return f"product:{product_id}"


def category_node(category_id: str) -> str:
    return f"category:{category_id}"


def review_node(review_id: str) -> str:
    return f"review:{review_id}"


def load_graph_data(file_path: str) -> dict:
    """Read the synthetic customer/review mapping JSON."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def _assign_ids(names: pd.Series, prefix: str) -> dict[str, str]:
    """Map each distinct non-missing name to prefix + 1, 2, ... in order of first appearance.

    Deterministic for the same input order, unlike Python's hash().
    """
    distinct = names.dropna().drop_duplicates().tolist()
    return {name: f"{prefix}{i}" for i, name in enumerate(distinct, start=1)}


def _customer_id(record: dict, source: str) -> str:
    """Return the record's customer_id, or raise if it is missing or blank."""
    value = record.get("customer_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing customer_id in {source}: {record}")
    return value.strip()


def build_knowledge_graph(
    orders_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    graph_data: dict,
) -> nx.DiGraph:
    """Build the directed knowledge graph.

    Args:
        orders_df: Orders already cleaned by normalize_orders() and fill_missing_categories().
        reviews_df: Reviews as loaded from data/reviews.json.
        graph_data: Synthetic mapping with "order_customers" and "review_relationships".

    Repeated purchases of the same product by one customer become a single
    "purchased" edge (a DiGraph keeps at most one edge per direction between two nodes).
    A product with a missing or conflicting category gets no "belongsTo" edge.
    Any reference to an unknown order, review, product or customer raises ValueError.
    """
    graph = nx.DiGraph()

    # Product and Category nodes, one per distinct cleaned name.
    product_ids = _assign_ids(orders_df["product"], "P")
    category_ids = _assign_ids(orders_df["category"], "CAT")

    for name, product_id in product_ids.items():
        graph.add_node(
            product_node(product_id),
            node_type="Product",
            product_id=product_id,
            product_name=name,
        )
    for name, category_id in category_ids.items():
        graph.add_node(
            category_node(category_id),
            node_type="Category",
            category_id=category_id,
            category_name=name,
        )

    # Product -belongsTo-> Category, only when the product has exactly one known category.
    known = orders_df.dropna(subset=["product", "category"])
    categories_per_product = known.groupby("product")["category"].unique()
    for name, categories in categories_per_product.items():
        if len(categories) == 1:
            graph.add_edge(
                product_node(product_ids[name]),
                category_node(category_ids[categories[0]]),
                relationship="belongsTo",
            )

    # Review nodes, copied unchanged from the review data.
    for review in reviews_df.to_dict("records"):
        graph.add_node(
            review_node(review["review_id"]),
            node_type="Review",
            review_id=review["review_id"],
            review_text=review["review_text"],
            reference_label=review["reference_label"],
            predicted_label=review["predicted_label"],
        )

    # Customer -purchased-> Product, via the synthetic order -> customer mapping.
    product_by_order = dict(zip(orders_df["order_id"], orders_df["product"]))
    seen_orders = set()
    for record in graph_data["order_customers"]:
        order_id = record.get("order_id")
        if order_id not in product_by_order:
            raise ValueError(f"order_customers references unknown order: {order_id!r}")
        if order_id in seen_orders:
            raise ValueError(f"Order {order_id!r} is assigned to more than one customer")
        seen_orders.add(order_id)

        product_name = product_by_order[order_id]
        if pd.isna(product_name):
            continue  # an order with no product name cannot be linked to a product node

        customer_id = _customer_id(record, "order_customers")
        graph.add_node(customer_node(customer_id), node_type="Customer", customer_id=customer_id)
        graph.add_edge(
            customer_node(customer_id),
            product_node(product_ids[product_name]),
            relationship="purchased",
        )

    # Customer -wrote-> Review and Review -about-> Product, via the synthetic review mapping.
    for record in graph_data["review_relationships"]:
        review_id = record.get("review_id")
        product_name = record.get("product_name")
        if not graph.has_node(review_node(str(review_id))):
            raise ValueError(f"review_relationships references unknown review: {review_id!r}")
        if product_name not in product_ids:
            raise ValueError(
                f"review_relationships references unknown product: {product_name!r}"
            )

        customer_id = _customer_id(record, "review_relationships")
        graph.add_node(customer_node(customer_id), node_type="Customer", customer_id=customer_id)
        graph.add_edge(customer_node(customer_id), review_node(review_id), relationship="wrote")
        graph.add_edge(
            review_node(review_id),
            product_node(product_ids[product_name]),
            relationship="about",
        )

    return graph


def summarize_graph(graph: nx.DiGraph) -> dict:
    """Count nodes per node_type and edges per relationship."""
    node_counts = Counter(attrs["node_type"] for _, attrs in graph.nodes(data=True))
    edge_counts = Counter(attrs["relationship"] for _, _, attrs in graph.edges(data=True))
    return {
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "node_types": {t: node_counts.get(t, 0) for t in NODE_TYPES},
        "relationships": {r: edge_counts.get(r, 0) for r in RELATIONSHIPS},
    }


def _has_relationship(graph: nx.DiGraph, source: str, target: str, relationship: str) -> bool:
    """True if the edge source -> target exists and has the given relationship."""
    edge = graph.get_edge_data(source, target)
    return edge is not None and edge.get("relationship") == relationship


def _is_node_type(graph: nx.DiGraph, node: str, node_type: str) -> bool:
    return graph.nodes[node].get("node_type") == node_type


def find_products_purchased_by_negative_reviewers(graph: nx.DiGraph) -> list[str]:
    """Names of all products bought by customers who wrote at least one negative review.

    A review is negative when its reference (ground-truth) label is "negative"; the LLM's
    predicted label is ignored. Every product a qualifying customer purchased is returned,
    not only the one they reviewed. Results are distinct and sorted alphabetically.
    The graph is only read, never modified.
    """
    # Step A: Review nodes whose reference label is negative.
    negative_reviews = [
        node
        for node, attrs in graph.nodes(data=True)
        if attrs.get("node_type") == "Review"
        and str(attrs.get("reference_label", "")).strip().lower() == "negative"
    ]

    # Step B: Customers with an incoming "wrote" edge to one of those reviews.
    negative_reviewers = set()
    for review in negative_reviews:
        for author in graph.predecessors(review):
            if _is_node_type(graph, author, "Customer") and _has_relationship(
                graph, author, review, "wrote"
            ):
                negative_reviewers.add(author)

    # Steps C and D: every product those customers purchased, collected in a set.
    product_names = set()
    for customer in negative_reviewers:
        for product in graph.successors(customer):
            if _is_node_type(graph, product, "Product") and _has_relationship(
                graph, customer, product, "purchased"
            ):
                product_names.add(graph.nodes[product]["product_name"])

    return sorted(product_names)


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent.parent / "data"

    orders = fill_missing_categories(normalize_orders(load_orders(str(data_dir / "orders.json"))))
    reviews = load_reviews(str(data_dir / "reviews.json"))
    graph_data = load_graph_data(str(data_dir / "graph_demo.json"))

    knowledge_graph = build_knowledge_graph(orders, reviews, graph_data)
    summary = summarize_graph(knowledge_graph)

    print("Knowledge Graph Summary")
    print("-----------------------")
    print(f"Total Nodes: {summary['total_nodes']}")
    print(f"Total Edges: {summary['total_edges']}")
    print("\nNode Types:")
    for node_type, count in summary["node_types"].items():
        print(f"{node_type}: {count}")
    print("\nRelationship Types:")
    for relationship, count in summary["relationships"].items():
        print(f"{relationship}: {count}")
