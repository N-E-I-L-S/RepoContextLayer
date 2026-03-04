import json
import os
from hybrid_search import search

with open("context_data/repo-context.json", "r", encoding="utf-8") as f:
    repo_context = json.load(f)

context_map = {}

for item in repo_context:
    if item["type"] == "method":
        key = f"{item['class']}::{item['method']}"
        context_map[key] = item
    elif item["type"] == "field":
        key = f"{item['class']}::{item['name']}"
        context_map[key] = item


def extract_snippet_method(file_path, start, end):
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    return code[start-1:end]

def extract_snippet_field(file_path, start, end):
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    return code[start-50:end+50]


def extract_snippets_from_results(query):
    semantic_hits, expanded_hits = search(query)
    print("=== Semantic Hits ===")
    for r in semantic_hits:
            print(r)

    print("\n=== Expanded Hits ===")
    for r in expanded_hits:
        print(r)
    all_methods = []
    all_fields = []
    for result in semantic_hits + expanded_hits:
        if result["type"] == "method":
            node = f"{result['class']}::{result['method']}"
            all_methods.append(node)
        elif result["type"] == "field":
            node = f"{result['class']}::{result['field']}"
            all_fields.append(node)
    
    all_fields = list(set(all_fields))
    all_methods = list(set(all_methods))

    snippets = []

    for node in all_methods + all_fields:
        if node not in context_map:
            continue

        ctx = context_map[node]

        if(ctx["type"] == "method"):
            snippet = extract_snippet_method(
            ctx["file"],
            ctx["startOffset"],
            ctx["endOffset"]
            )
        elif(ctx["type"] == "field"):
            snippet = extract_snippet_field(
            ctx["file"],
            ctx["startOffset"],
            ctx["endOffset"]
            )

        if snippet:
            if(ctx["type"] == "method"):
                snippets.append({
                    "id": ctx["id"],
                    "class": ctx["class"],
                    "method": ctx["method"],
                    "file": ctx["file"],
                    "code": snippet
                })
            elif(ctx["type"] == "field"):
                snippets.append({
                    "id": ctx["id"],
                    "class": ctx["class"],
                    "field": ctx["name"],
                    "file": ctx["file"],
                    "code": snippet
                })

    return snippets

if __name__ == "__main__":
    query = "Add one more attribute to create Product entity"

    snippets = extract_snippets_from_results(query)

    print("\n=== Extracted Code Snippets ===\n")

    for s in snippets:
        if "method" in s:
            print(f"\n--- {s['class']}::{s['method']} ---")
        elif "field" in s:
            print(f"\n--- {s['class']}::{s['field']} ---")
        print(s["code"])