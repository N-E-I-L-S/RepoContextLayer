import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")


def detect_service(file_path):
    parts = file_path.split("/")
    return parts[1] if len(parts) > 1 else parts[0]


def normalize_path(path):
    return path.replace("\\", "/")


with open("parser/context_data/repo-context.json", "r", encoding="utf-8") as f:
    repo = json.load(f)

documents = []
metadata = []

# -------------------------
# Create documents
# -------------------------

for item in repo:

    service = detect_service(normalize_path(item["file"]))

    # ---------------- METHOD ----------------

    if item["type"] == "method":

        call_list = []

        for c in item.get("calls", []):
            if isinstance(c, dict):
                call_list.append(c["target"])
            else:
                call_list.append(c)

        doc = f"""
Spring microservice method.

Service: {service}
Layer: {item.get('layer','')}

Class: {item['class']}
Method: {item['method']}
Return Type: {item.get('returnType','')}

Calls:
{', '.join(call_list)}

Reads:
{', '.join(item.get('reads', []))}

Writes:
{', '.join(item.get('writes', []))}
Annotations:
{', '.join(item.get('annotations', []))}
"""

        documents.append(doc.strip())

        metadata.append({
            "id": item["id"],
            "type": "method",
            "layer": item.get("layer"),
            "service": service,
            "class": item["class"],
            "method": item["method"],
            "file": normalize_path(item["file"])
        })

    # ---------------- CLASS ----------------

    elif item["type"] == "class":

        field_list = [
            f"{f['name']} ({f['type']})"
            for f in item.get("fields", [])
        ]

        injection_list = [
            f"{inj['field']} ({inj['type']})"
            for inj in item.get("injections", [])
        ]

        doc = f"""
Spring microservice class.

Service: {service}
Layer: {item.get('layer','')}

Class: {item['class']}

Fields:
{', '.join(field_list)}

Injected Dependencies:
{', '.join(injection_list)}

Methods:
{', '.join(item.get('methods', []))}
"""

        documents.append(doc.strip())

        metadata.append({
            "id": item["id"],
            "type": "class",
            "layer": item.get("layer"),
            "service": service,
            "class": item["class"],
            "file": normalize_path(item["file"])
        })

    # ---------------- REPOSITORY ----------------

    elif item["type"] == "repository":

        doc = f"""
Spring Data repository.

Service: {service}

Repository: {item['class']}
Model: {item.get('model','')}
"""

        documents.append(doc.strip())

        metadata.append({
            "id": item["id"],
            "type": "repository",
            "service": service,
            "repository": item["class"],
            "model": item.get("model"),
            "file": normalize_path(item["file"])
        })

    # ---------------- MODEL ----------------

    elif item["type"] == "model":

        doc = f"""
JPA entity model.

Service: {service}

Model Class: {item['id']}
"""

        documents.append(doc.strip())

        metadata.append({
            "id": item["id"],
            "type": "model",
            "service": service,
            "class": item["id"],
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
# FAISS index
# -------------------------

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

faiss.write_index(index, "parser/context_data/repo_index.faiss")

with open("parser/context_data/repo_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print("✅ Embeddings + FAISS index saved.")