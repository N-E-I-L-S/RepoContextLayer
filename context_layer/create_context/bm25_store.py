import re
import json
import pickle
from rank_bm25 import BM25Okapi
import os 

configPath = os.path.join(os.path.dirname(__file__), "config.json")
with open(configPath, "r") as f:
    config = json.load(f)

CONTEXT_DATA_PATH = config["context_data"]["path"]

file_path = f"{CONTEXT_DATA_PATH}repo-context.json"
with open(file_path, "r", encoding="utf-8") as f:
    repo_context = json.load(f)

list_to_remove = ["id", "layer", "location", "reads", "writes"]

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


documents = []

for item in repo_context:

    obj = item.copy()

    for key in list_to_remove:
        obj.pop(key, None)

    if "file" in obj:
        obj["file"] = obj["file"].split("\\")[-1].replace(".java", "")

    tokens = []

    for v in obj.values():

        if isinstance(v, list):
            tokens.extend([str(x) for x in v if not isinstance(x, dict)])

        elif isinstance(v, (str, int, float, bool)):
            tokens.append(str(v))

    # ignore dicts or complex objects

    item_text = " ".join(tokens)

    item_text = item_text.replace(".", " ")

    item_text = split_camel_keep_original(item_text)

    item_text = item_text.lower()

    item_text = item_text.translate(str.maketrans("", "", "!\"#$%&'()*+,-/:;<=>?@[\\]^_`{|}~"))

    item_text = " ".join([w for w in item_text.split() if w not in stop_words])

    documents.append(item_text)


tokenized_docs = [doc.split() for doc in documents]

bm25 = BM25Okapi(tokenized_docs)

# Save index
with open(f"{CONTEXT_DATA_PATH}bm25_index.pkl", "wb") as f:
    pickle.dump({
        "bm25": bm25,
        "documents": documents,
    }, f)

print("BM25 index saved")