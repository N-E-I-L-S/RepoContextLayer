import json

with open("context_data/repo-context.json", "r", encoding="utf-8") as f:
    repo = json.load(f)

graph = {}
reverse_graph = {}

# Build method index first
method_index = {}

for item in repo:
    if item["type"] == "method":
        full_name = f"{item['class']}.{item['method']}"
        method_index[item["method"]] = full_name
        graph[full_name] = []

# Build edges
for item in repo:
    if item["type"] == "method":

        source = f"{item['class']}.{item['method']}"

        for call in item.get("calls", []):
            if call in method_index:
                target = method_index[call]

                graph[source].append(target)
                reverse_graph.setdefault(target, []).append(source)

with open("context_data/call_graph.json", "w", encoding="utf-8") as f:
    json.dump({
        "forward": graph,
        "reverse": reverse_graph
    }, f, indent=2)

print("✅ Graph index built.")