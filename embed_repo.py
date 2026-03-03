import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def detect_service(file_path):
    file_path = file_path.replace("\\", "/")  # Normalize for Windows paths
    return file_path.split("/")[0]

def normalize_path(path):
    return path.replace("\\", "/")
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

with open("repo-context.json", "r", encoding="utf-8") as f:
    repo = json.load(f)

documents = []
metadata = []

# -------------------------
# Build semantic documents
# -------------------------

def build_class_doc(file_entry, cls):
    service = detect_service(file_entry["file"])

    field_names = []
    for f in cls.get("fields", []):
        if isinstance(f, dict):
            field_names.append(f"{f.get('type')} {f.get('name')}")

    method_names = [m["name"] for m in cls.get("methods", [])]

    resolved_targets = []
    for m in cls.get("methods", []):
        for r in m.get("resolvedCalls", []):
            resolved_targets.append(r["to"])

    doc = f"""
    Spring microservice class.

    Service: {service}
    Class: {cls['name']}
    Package: {file_entry.get('package','')}

    Fields:
    {', '.join(field_names)}

    Methods:
    {', '.join(method_names)}

    Outgoing Dependencies:
    {', '.join(set(resolved_targets))}
    """

    return doc.strip()

def build_method_doc(file_entry, cls, method):
    service = detect_service(file_entry["file"])

    calls = [
        f"{c.get('object','')}.{c.get('method','')}"
        for c in method.get("calls", [])
        if c.get("method")
    ]

    resolved = [
        r.get("to")
        for r in method.get("resolvedCalls", [])
    ]

    doc = f"""
    Spring microservice method.

    Service: {service}
    Class: {cls['name']}
    Method: {method['name']}
    Signature: {method.get('signature','')}

    Direct Calls:
    {', '.join(calls)}

    Resolved Dependencies:
    {', '.join(resolved)}
    """

    return doc.strip()

# -------------------------
# Create documents
# -------------------------
# -------------------------
# Create documents (FLAT STRUCTURE)
# -------------------------

for item in repo:
    service = detect_service(item["file"])

    if item["type"] == "field":
        doc = f"""
        Spring microservice field.

        Service: {service}
        Class: {item['class']}
        Field: {item['name']}
        Type: {item.get('fieldType','')}
        """

        documents.append(doc.strip())
        metadata.append({
            "type": "field",
            "service": service,
            "class": item["class"],
            "field": item["name"],
            "file": normalize_path(item["file"])
        })

    elif item["type"] == "method":
        doc = f"""
        Spring microservice method.

        Service: {service}
        Class: {item['class']}
        Method: {item['method']}
        Return Type: {item.get('returnType','')}

        Direct Calls:
        {', '.join(item.get('calls', []))}

        Reads:
        {', '.join(item.get('reads', []))}

        Writes:
        {', '.join(item.get('writes', []))}
        """

        documents.append(doc.strip())
        metadata.append({
            "type": "method",
            "service": service,
            "class": item["class"],
            "method": item["method"],
            "file": normalize_path(item["file"])
        })

print(f"Created {len(documents)} documents.")

# -------------------------
# Generate embeddings
# -------------------------

embeddings = model.encode(
    documents,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)

embeddings = np.array(embeddings).astype("float32")

print("Embedding shape:", embeddings.shape)

# -------------------------
# Store in FAISS
# -------------------------

dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # cosine similarity (since normalized)

index.add(embeddings)

faiss.write_index(index, "repo_index.faiss")

# Save metadata
with open("repo_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print("✅ Embeddings + FAISS index saved.")