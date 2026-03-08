import json

with open("repo-graph.json") as f:
    data = json.load(f)

nodes = []
links = []

for node_id, node in data.items():

    nodes.append({
        "id": node_id,
        "layer": node.get("layer", "unknown")
    })

    for edge in node.get("edges", []):
        links.append({
            "source": node_id,
            "target": edge["to"]
        })

graph = {
    "nodes": nodes,
    "links": links
}

with open("graph_viz.json", "w") as f:
    json.dump(graph, f, indent=2)