import json
import pickle
import re

with open("config.json", "r") as f:
    config = json.load(f)

CONTEXT_DATA_PATH = config["context_data"]["path"]

with open(f"{CONTEXT_DATA_PATH}bm25_index.pkl", "rb") as f:
    data = pickle.load(f)

bm25 = data["bm25"]
documents = data["documents"]
with open(f"{CONTEXT_DATA_PATH}repo-context.json", "r", encoding="utf-8") as f:
    repo_context = json.load(f)

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

def bm25_search(query, top_k=1):

    tokens = preprocess_query(query)
    scores = bm25.get_scores(tokens)
    ranked = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    results = [repo_context[i] for i in ranked]

    return results

results = bm25_search("product service create product method")

for r in results:
    print(r)