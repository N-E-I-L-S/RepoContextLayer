@echo off
set BASE=create_context\
echo "Parsing repository..."
call node "%BASE%scan_repo.js" || goto :error
call node "%BASE%parse_java.js" || goto :error
call node "%BASE%extract_imports.js" || goto :error
call node "%BASE%build_class_index.js" || goto :error
call node "%BASE%resolve_di.js" || goto :error
call node "%BASE%resolve_types.js" || goto :error

call python "%BASE%build_call_graph.py" || goto :error
echo "Building embeddings and FAISS index..."
call python "%BASE%embed_repo.py" || echo EMBEDDING_ERROR 

echo "BM25 index generation..."
call python "%BASE%bm25_store.py" || goto :error
echo Pipeline completed!
exit /b 0

:error
echo Error occurred. Stopping pipeline.
pause
exit /b 1