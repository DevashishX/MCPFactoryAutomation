@echo off

echo Starting FastMCP Servers...

REM Start RAG server in a new window
start "RAG Server" /D "%~dp0" ".conda\python.exe" rag_fastmcp_server.py --transport http

REM Start Orchestrator server in a new window
start "Orchestrator Server" /D "%~dp0" ".conda\python.exe" orchestrator_fastmcp_server.py --transport http

echo Both servers started in separate windows.