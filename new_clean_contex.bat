@echo off

echo Cleaning context data...
DEL parser\context_data\call_graph.json
DEL parser\context_data\class-index.json
DEL parser\context_data\di-map.json
DEL parser\context_data\files.json
DEL parser\context_data\imports.json
DEL parser\context_data\repo_index.faiss
DEL parser\context_data\repo_metadata.json
DEL parser\context_data\repo-context.json
DEL parser\context_data\repo-context.md
DEL parser\context_data\resolved-types.json