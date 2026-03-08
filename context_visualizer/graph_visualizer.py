import json
import networkx as nx
from pyvis.network import Network

# -------------------------
# Load graph JSON
# -------------------------
with open("../parser/context_data/call_graph.json", "r", encoding="utf-8") as f:
    data = json.load(f)

forward = data["forward"]

# -------------------------
# Build graph
# -------------------------

G = nx.DiGraph()

for caller, callees in forward.items():
    G.add_node(caller)

    for callee in callees:
        G.add_edge(caller, callee)

print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())

# -------------------------
# Create interactive graph
# -------------------------

net = Network(
    height="900px",
    width="100%",
    bgcolor="#111111",
    font_color="white",
    directed=True
)
net.toggle_physics(False)
# Enable physics for better spreading
net.barnes_hut()

# Import networkx graph
net.from_nx(G)

# -------------------------
# Save HTML
# -------------------------

net.show("call_graph.html", notebook=False)

print("Open call_graph.html in browser")