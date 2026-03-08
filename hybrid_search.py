import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

TOP_K = 5
GRAPH_EXPANSION_DEPTH = 2

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# Load FAISS
index = faiss.read_index("parser/context_data/repo_index.faiss")

with open("parser/context_data/repo_metadata.json") as f:
    metadata = json.load(f)

with open("parser/context_data/call_graph.json") as f:
    graph_data = json.load(f)

forward_graph = graph_data["forward"]
reverse_graph = graph_data["reverse"]


def expand_graph(nodes, depth=1):
    visited = set(nodes)
    frontier = set(nodes)

    for _ in range(depth):
        new_nodes = set()

        for node in frontier:
            for nxt in forward_graph.get(node, []):
                if nxt not in visited:
                    new_nodes.add(nxt)

            for prev in reverse_graph.get(node, []):
                if prev not in visited:
                    new_nodes.add(prev)

        visited.update(new_nodes)
        frontier = new_nodes

    return visited

def search(query):
    query_vec = model.encode([query], normalize_embeddings=True)
    D, I = index.search(np.array(query_vec).astype("float32"), TOP_K)

    semantic_hits = []
    graph_seeds = []

    for rank, idx in enumerate(I[0]):
        score = float(D[0][rank])
        meta = metadata[idx]

        result = {
            "score": round(score, 4),
            **meta
        }

        semantic_hits.append(result)

        if meta["type"] == "method":
            graph_seeds.append(f"{meta['class']}::{meta['method']}")

    # Graph expansion
    expanded_nodes = expand_graph(graph_seeds, GRAPH_EXPANSION_DEPTH)

    expanded_results = []

    for meta in metadata:
        if meta["type"] == "method":
            node = f"{meta['class']}::{meta['method']}"
            if node in expanded_nodes:
                expanded_results.append(meta)

    return semantic_hits, expanded_results

if __name__ == "__main__":
    semantic, expanded = search("change return type of placeOrder to return boolean")

    print("\n=== Semantic Top K (with scores) ===")
    for r in semantic:
        print(r)

    print("\n=== After Graph Expansion ===")
    for r in expanded:
        print(r)