@echo off
set BASE=search\
@REM echo "Starting search pipeline..."
@REM call python "%BASE%hybrid_search.py" || goto :error
echo "Extracting code snippets..."
call python "%BASE%code_extractor.py" || goto :error
exit /b 0

:error
echo Error occurred. Stopping pipeline.
pause
exit /b 1