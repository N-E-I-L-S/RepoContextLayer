import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

index = faiss.read_index("context_data/repo_index.faiss")

with open("context_data/repo_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

def search(query, top_k=5):
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).astype("float32")

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for idx, score in zip(indices[0], scores[0]):
        results.append({
            "score": float(score),
            "metadata": metadata[idx]
        })

    return results

results = search("Add one more filter in User Authentication", 10)

for r in results:
    print(r)