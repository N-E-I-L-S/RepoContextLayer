@echo off

if exist "context_data\repo_metadata.json" (
    echo Cleaning repo_metadata.json...
    del /f /q "context_data\repo_metadata.json"
)

if exist "context_data\repo-graph.json" (
    echo Cleaning repo-graph.json...
    del /f /q "context_data\repo-graph.json"
)

if exist "context_data\call_graph.json" (
    echo Cleaning call_graph.json...
    del /f /q "context_data\call_graph.json"
)

if exist "context_data\repo-context.json" (
    echo Cleaning repo-context.json...
    del /f /q "context_data\repo-context.json"
)

if exist "context_data\repo_index.faiss" (
    echo Cleaning repo_index.faiss...
    del /f /q "context_data\repo_index.faiss"
)