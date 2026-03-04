const fs = require("fs");

const nodes = JSON.parse(fs.readFileSync("context_data/repo-context.json", "utf8"));

const graph = {};

for (const node of nodes) {
  graph[node.id] = {
    ...node,
    calls: [],
    calledBy: [],
    reads: node.reads || [],
    writes: node.writes || [],
  };
}

// Build method call edges
for (const node of nodes) {
  if (node.type === "method") {
    for (const call of node.calls || []) {
      const target = Object.values(graph).find(
        (n) => n.type === "method" && n.method === call
      );

      if (target) {
        graph[node.id].calls.push(target.id);
        graph[target.id].calledBy.push(node.id);
      }
    }
  }
}

fs.writeFileSync("context_data/repo-graph.json", JSON.stringify(graph, null, 2));

console.log("repo-graph.json generated.");