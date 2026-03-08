import json
import os
from hybrid_search import search

with open("context_data/repo-context.json", "r", encoding="utf-8") as f:
    repo_context = json.load(f)

context_map = {}

# Map every node by id
for item in repo_context:
    context_map[item["id"]] = item


def extract_snippet(file_path, start, end):
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return "".join(lines[start-1:end])


def extract_snippets_from_results(query):
    semantic_hits, expanded_hits = search(query)

    print("=== Semantic Hits ===")
    for r in semantic_hits:
        print(r)

    print("\n=== Expanded Hits ===")
    for r in expanded_hits:
        print(r)

    snippets = []
    seen_ids = set()

    for result in semantic_hits + expanded_hits:

        node_id = result["id"]

        if node_id in seen_ids:
            continue
        seen_ids.add(node_id)

        if node_id not in context_map:
            continue

        ctx = context_map[node_id]

        snippet = extract_snippet(
            ctx["file"],
            ctx["location"]["start"]["line"],
            ctx["location"]["end"]["line"]
        )

        if snippet:
            snippets.append({
                "id": ctx["id"],
                "class": ctx.get("class"),
                "file": ctx["file"],
                "start_line": ctx["location"]["start"]["line"],
                "end_line": ctx["location"]["end"]["line"],
                "code": snippet
            })

    return snippets


if __name__ == "__main__":

    query = "Add one more attribute to Product entity"

    snippets = extract_snippets_from_results(query)

    print("\n=== Extracted Code Snippets ===\n")

    for s in snippets:
        print(f"\n--- ({s['file']}:{s['start_line']}-{s['end_line']}) ---")
        print(s["code"])