const fs = require("fs");

const nodes = JSON.parse(
  fs.readFileSync("context_data/repo-context.json", "utf8")
);

const graph = {};
const methodIndex = {};
const fieldIndex = {};

// -----------------------------
// Build graph node structure
// -----------------------------

for (const node of nodes) {
  graph[node.id] = {
    ...node,
    calls: [],
    calledBy: [],
    reads: Array.isArray(node.reads) ? node.reads : [],
    writes: Array.isArray(node.writes) ? node.writes : [],
    edges: []
  };

  // Build method lookup
  if (node.type === "method" && node.method) {
    if (!methodIndex[node.method]) {
      methodIndex[node.method] = [];
    }
    methodIndex[node.method].push(node.id);
  }

  // Build field lookup
  if (node.type === "field") {
    const key = `${node.class}.${node.name}`;
    fieldIndex[key] = node.id;
  }
}

// -----------------------------
// Method → Method calls
// -----------------------------

for (const node of nodes) {

  if (node.type !== "method") continue;

  const source = graph[node.id];

  const calls = Array.isArray(node.calls) ? node.calls : [];

  for (let call of calls) {

    if (!call) continue;

    // normalize call like object.method
    if (call.includes(".")) {
      call = call.split(".").pop();
    }

    const targets = methodIndex[call];

    if (!Array.isArray(targets)) continue;

    for (const targetId of targets) {

      source.calls.push(targetId);

      graph[targetId].calledBy.push(node.id);

      source.edges.push({
        type: "method_call",
        to: targetId
      });

    }
  }
}

// -----------------------------
// Method → Field reads/writes
// -----------------------------

for (const node of nodes) {

  if (node.type !== "method") continue;

  const source = graph[node.id];

  const reads = Array.isArray(node.reads) ? node.reads : [];
  const writes = Array.isArray(node.writes) ? node.writes : [];

  for (const field of reads) {

    const fieldId = fieldIndex[field];

    if (!fieldId) continue;

    source.edges.push({
      type: "field_read",
      to: fieldId
    });
  }

  for (const field of writes) {

    const fieldId = fieldIndex[field];

    if (!fieldId) continue;

    source.edges.push({
      type: "field_write",
      to: fieldId
    });
  }
}

// -----------------------------
// Repository → Model relation
// -----------------------------

for (const node of nodes) {

  if (node.layer !== "repository") continue;

  if (!node.repositoryEntity) continue;

  const model = nodes.find(
    n => n.layer === "model" && n.class === node.repositoryEntity
  );

  if (!model) continue;

  graph[node.id].edges.push({
    type: "repository_entity",
    to: model.id
  });
}

// -----------------------------
// Save graph
// -----------------------------

fs.writeFileSync(
  "context_data/repo-graph.json",
  JSON.stringify(graph, null, 2)
);

console.log("✅ repo-graph.json generated.");