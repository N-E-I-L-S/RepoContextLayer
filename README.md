# ContextLayer – Repository Intelligence Engine

ContextLayer is a static analysis + semantic search + dependency graph engine for Java microservices.

It parses Java repositories, extracts structural information (classes, methods, fields), builds dependency graphs, generates semantic embeddings, and enables intelligent code retrieval for LLM-powered workflows.

This project is designed for use cases like:

- “Write a loader for `User.email`”
- “Find all writers of `Order.status`”
- “Show all methods dependent on this attribute”
- “Generate service layer for this entity”
- “Expand dependencies of this method across microservices”

---

# Architecture Overview

Pipeline:

Java Repository
↓
analyze_repo.js
↓
repo-context.json
↓
build_graph.py
↓
call_graph.json
↓
embed_repo.py


Remove field only nodes -> move fields inside classes and methods
Implement BM25 for keyword matching

Class node schema:
{
  "id": "InventoryService",
  "type": "class",
  "layer": "service",
  "class": "InventoryService",
  "file": "inventory-service/src/.../InventoryService.java",

  "annotations": [List_of_annotations],

  "fields": [
    {
      "name": "inventoryRepository",
      "type": "InventoryRepository"
    }
  ],

  "injections": [
    {
      "field": "inventoryRepository",
      "type": "InventoryRepository"
    }
  ],

  "methods": [
    "InventoryService.updateStock",
    "InventoryService.getInventory"
  ],

  "location": {
    "start": { "line": 1 },
    "end": { "line": 120 }
  }
}

Method node:
{
  "id": "InventoryService.updateStock",
  "type": "method",

  "layer": "service",

  "class": "InventoryService",
  "method": "updateStock",

  "returnType": "Inventory",

  "parameters": [
    "Long id",
    "int quantity"
  ],

  "annotations": ["Transactional"],

  "calls": [
    "InventoryRepository.save"
  ],

  "reads": [
    "Inventory.quantity"
  ],

  "writes": [
    "Inventory.quantity"
  ],

  "file": "inventory-service/src/.../InventoryService.java",

  "location": {
    "start": { "line": 40 },
    "end": { "line": 70 }
  }
}

Repo Node:
{
  "id": "InventoryRepository",
  "type": "repository",
  "layer": "repository",
  "class": "InventoryRepository",
  "model": "Inventory",
  "file": "...",
  "location": {...}
}

Model node:
{
  "id": "Inventory",
  "type": "model",
  "layer": "model",

  "fields": [
    { "name": "id", "type": "Long" },
    { "name": "quantity", "type": "int" }
  ],

  "file": "...",
  "location": {...}
}