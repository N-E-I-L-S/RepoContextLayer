@echo off

echo "Cleaning up repo_metadata.json..."
DEL repo_metadata.json

echo "Cleaning up repo-graph.json..."
DEL repo-graph.json

echo "Cleaning up call_graph.json..."
DEL call_graph.json

echo "Cleaning up repo-context.json and Index..."
DEL repo-context.json
DEL repo_index.faiss