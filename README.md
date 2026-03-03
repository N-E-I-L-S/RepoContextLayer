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
