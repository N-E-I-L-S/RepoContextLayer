import json
import os
from hybrid_search import search

class CodeProvider:
    def __init__(self, repo_context_path="repo-context.json"):
        # Load repo-context into memory
        with open(repo_context_path, "r", encoding="utf-8") as f:
            self.repo_context = json.load(f)

    def get_snippet(self, symbol_id):
        """Fetch a snippet for a single symbol using startOffset/endOffset"""
        doc = next((d for d in self.repo_context if d["id"] == symbol_id), None)
        if not doc:
            return None

        file_path = doc["file"].replace("\\", os.sep)
        start = doc.get("startOffset")
        end = doc.get("endOffset")
        if start is None or end is None:
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
                return code[start:end]
        except FileNotFoundError:
            return None

    def get_snippets_for_symbols(self, symbol_ids):
        """Fetch snippets for multiple symbols"""
        snippets = {}
        for sid in symbol_ids:
            snippet = self.get_snippet(sid)
            if snippet:
                snippets[sid] = snippet
        return snippets


def fetch_snippets_for_query(user_query):
    """
    Run hybrid_search for a user query, fetch all retrieved documents
    from repo_metadata, then get their code snippets using repo-context
    """
    # 1. Run search
    semantic_hits, _ = search(user_query)
    if not semantic_hits:
        print("[!] No search hits found.")
        return {}

    # 2. Collect symbol_ids from search hits
    symbol_ids = []
    for hit in semantic_hits:
        method = hit.get("method")
        field = hit.get("field")
        cls = hit.get("class")
        if method:
            symbol_ids.append(f"{cls}.{method}")
        elif field:
            symbol_ids.append(f"{cls}.{field}")

    # 3. Initialize provider and fetch snippets
    provider = CodeProvider("repo-context.json")
    snippets = provider.get_snippets_for_symbols(symbol_ids)

    return snippets


# Example usage
if __name__ == "__main__":
    user_query = "Add one more filter in User Authentication"
    snippets = fetch_snippets_for_query(user_query)

    print(f"Fetched {len(snippets)} code snippets for query: '{user_query}'\n")
    for sid, code in snippets.items():
        print(f"\n--- {sid} ---\n{code}\n")