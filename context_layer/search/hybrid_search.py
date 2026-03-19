import json
import pickle
import re
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# ---------------- CONFIG ---------------- #

BASE_DIR = os.path.dirname(__file__)

with open(os.path.join(BASE_DIR, "config.json")) as f:
    config = json.load(f)

CONTEXT_DATA_PATH = config["context_data"]["path"]

TOP_K = 5
GRAPH_DEPTH = 2

# ---------------- LOAD ---------------- #

# BM25
with open(f"{CONTEXT_DATA_PATH}bm25_index.pkl", "rb") as f:
    bm25_data = pickle.load(f)

bm25 = bm25_data["bm25"]
documents = bm25_data["documents"]

# Repo context (BM25 uses this)
with open(f"{CONTEXT_DATA_PATH}repo-context.json") as f:
    repo_context = json.load(f)

# FAISS
index = faiss.read_index(f"{CONTEXT_DATA_PATH}repo_index.faiss")

with open(f"{CONTEXT_DATA_PATH}repo_metadata.json") as f:
    metadata = json.load(f)

# Graph
with open(f"{CONTEXT_DATA_PATH}call_graph.json") as f:
    graph_data = json.load(f)

forward_graph = graph_data["forward"]
reverse_graph = graph_data["reverse"]

# Model
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# ---------------- BM25 ---------------- #

stop_words = set([
    "string","int","boolean","void","double","float","char","long",
    "short","byte","bean","list","map","set","queue","deque",
    "collection","arraylist","linkedlist","hashmap","hashset",
    "treemap","treeset","name","type"
])

def split_camel_keep_original(text):
    tokens = []
    for word in text.split():
        tokens.append(word)
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', word)
        if len(parts) > 1:
            tokens.extend(parts)
    return " ".join(tokens)

def preprocess_query(query):
    query = query.replace(".", " ")
    query = split_camel_keep_original(query)
    query = query.lower()
    query = query.translate(str.maketrans("", "", "!\"#$%&'()*+,-/:;<=>?@[\\]^_`{|}~"))
    query = " ".join([w for w in query.split() if w not in stop_words])
    return query.split()

def bm25_search(query, top_k=TOP_K):
    tokens = preprocess_query(query)
    scores = bm25.get_scores(tokens)

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    return [(rank, scores[rank]) for rank in ranked]

# ---------------- SEMANTIC ---------------- #

def semantic_search(query, top_k=TOP_K):
    query_vec = model.encode([query], normalize_embeddings=True)
    D, I = index.search(np.array(query_vec).astype("float32"), top_k)

    results = []
    for rank, idx in enumerate(I[0]):
        score = float(D[0][rank])
        results.append((idx, score))

    return results

# ---------------- FUSION (RRF) ---------------- #

def reciprocal_rank_fusion(bm25_res, semantic_res, k=60):
    scores = {}

    for rank, (idx, _) in enumerate(bm25_res):
        scores[idx] = scores.get(idx, 0) + 1 / (k + rank)

    for rank, (idx, _) in enumerate(semantic_res):
        scores[idx] = scores.get(idx, 0) + 1 / (k + rank)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in ranked]

# ---------------- GRAPH ---------------- #

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

# ---------------- FINAL SEARCH ---------------- #

def hybrid_search(query):
    # 1. BM25 + Semantic
    bm25_res = bm25_search(query)
    semantic_res = semantic_search(query)

    # 2. Fuse
    fused_indices = reciprocal_rank_fusion(bm25_res, semantic_res)

    # 3. Take top seeds
    top_indices = fused_indices[:TOP_K]

    seeds = []
    results = []

    for idx in top_indices:
        meta = metadata[idx]
        results.append(meta)

        if meta["type"] == "method":
            seeds.append(f"{meta['class']}::{meta['method']}")

    # 4. Graph expansion
    expanded_nodes = expand_graph(seeds, GRAPH_DEPTH)

    expanded_results = []
    for meta in metadata:
        if meta["type"] == "method":
            node = f"{meta['class']}::{meta['method']}"
            if node in expanded_nodes:
                expanded_results.append(meta)

    return results, expanded_results


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    base, expanded = hybrid_search("create product in product service")

    print("\n=== HYBRID TOP RESULTS ===")
    for r in base:
        print(r)

    print("\n=== AFTER GRAPH EXPANSION ===")
    for r in expanded:
        print(r)