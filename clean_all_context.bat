@echo off

echo "Cleaning up repo_metadata.json..."
DEL /context_data/repo_metadata.json

echo "Cleaning up repo-graph.json..."
DEL /context_data/repo-graph.json

echo "Cleaning up call_graph.json..."
DEL /context_data/call_graph.json

echo "Cleaning up repo-context.json and Index..."
DEL /context_data/repo-context.json
DEL /context_data/repo_index.faiss