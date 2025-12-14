# MCPFactoryAutomation

## PCB Assembly Orchestrator

A visual orchestrator for PCB assembly processes with MCP (Model Context Protocol) integration for Claude Desktop.

## Features

- Visual workflow designer for PCB assembly sequences
- 5-step process orchestration with configurable parameters
- Real-time validation against predefined patterns
- RAG (Retrieval-Augmented Generation) system for process documentation
- MCP server integration via HTTP (recommended) or stdio
- FastMCP implementation for both orchestrator and RAG servers

## Installation

1. Navigate to the project directory:
   ```bash
   cd path/to/MCPFactoryAutomation
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Copy `.env.example` to `.env` and configure Ollama settings for RAG

## Running the Servers

### Start Both Servers (Recommended)
```bash
start_servers.sh
```

```bash
start_servers.bat
```
This starts both the orchestrator (port 8000) and RAG server (port 8001) via HTTP.

### Run Individually
```bash
# Orchestrator server (HTTP)
python orchestrator_fastmcp_server.py --transport http --port 8000

# RAG server (HTTP)
python rag_fastmcp_server.py --transport http --port 8001

# Or with stdio (alternative)
python orchestrator_fastmcp_server.py --transport stdio
python rag_fastmcp_server.py --transport stdio
```

## Claude Desktop Configuration

Add to your config file: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

### HTTP Configuration (Recommended)
```json
{
  "mcpServers": {
    "pcb-orchestrator": {
      "url": "http://127.0.0.1:8000/mcp"
    },
    "pcb-rag": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

## Available MCP Tools

### Orchestrator Tools
- `set_block_at_position` - Set block type at a specific position
- `set_sub_param_at_position` - Configure sub-parameters
- `get_current_process` - View current configuration
- `execute_process` - Execute valid sequences
- `get_current_process_validity` - Check sequence validity
- `get_valid_processes` - List all valid processes
- `get_block_sub_params` - Query valid parameters for blocks
- `get_possible_blocks_sub_params` - Get all blocks and their parameters

### RAG Tools
- `get_query_rag` - Search process documentation with natural language queries

## Valid Processes

The orchestrator supports predefined valid processes in file [processes.py](./processes.py)




```
