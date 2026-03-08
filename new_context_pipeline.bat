@echo off

echo 1. Scanning Repo...
cd parser
mkdir context_data 2>nul
node scan_repo.js

echo 2. Repo scanned, creating imports directory...
node extract_imports.js

echo 3. Imports extracted, Parsing java files...
node parse_java.js

echo 4. Java files parsed, building class index...
node build_class_index.js

echo 5. Class index built, resolving DI...
node resolve_di.js

echo 6. DI resolved, resolving types...
node resolve_types.js

echo 7. Types resolved, building call graph...
python build_call_graph.py

cd ../
echo 8. Call graph built. Starting to build vector database...
python embed_repo.py

