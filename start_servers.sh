#!/bin/bash
python rag_fastmcp_server.py --transport http &
python orchestrator_fastmcp_server.py --transport http &

