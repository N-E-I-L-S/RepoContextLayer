@echo off

mkdir context_data
echo "Starting Code Parser..."
node analyze-repo.js

echo "Code Parser finished, created repo-context. Starting to build repo-graph..."
@REM node build_graph.js

echo "repo-graph built. Starting to build call_graph..."
python graph-index.py

echo "Call graph built. Starting to build vector database..."
python embed_repo.py

