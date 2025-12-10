"""
MCP Server for PCB Assembly Orchestrator

This server exposes the orchestrator manipulation functions to Claude via MCP protocol.
"""

import asyncio
import threading
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Import the GUI application
from orchestrator_gui import OrchestratorApp

# Global app instance
app_instance = None

# Create MCP server
server = Server("orchestrator-server")

def start_gui_thread():
    """Start the GUI in a separate thread"""
    global app_instance
    app_instance = OrchestratorApp()
    app_instance.run()

# Start GUI in background thread when server starts
gui_thread = threading.Thread(target=start_gui_thread, daemon=True)
gui_thread.start()

# Wait for app to initialize
import time
time.sleep(1)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available tools for orchestrator manipulation"""
    return [
        types.Tool(
            name="set_block_at_position",
            description="Set a specific block type at a given position (0-4). Valid blocks: 'Solder Paste Application', 'Component Placement', 'Soldering', 'Optical Inspection', 'Functional Testing'",
            inputSchema={
                "type": "object",
                "properties": {
                    "pos": {
                        "type": "integer",
                        "description": "Position (0-4)",
                        "minimum": 0,
                        "maximum": 4
                    },
                    "block_type": {
                        "type": "string",
                        "description": "Block type name",
                        "enum": ["Solder Paste Application", "Component Placement", "Soldering", "Optical Inspection", "Functional Testing"]
                    }
                },
                "required": ["pos", "block_type"]
            }
        ),
        types.Tool(
            name="set_sub_param_at_position",
            description="Set a sub-parameter at a given position (0-4). Valid sub-params depend on the block type at that position.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pos": {
                        "type": "integer",
                        "description": "Position (0-4)",
                        "minimum": 0,
                        "maximum": 4
                    },
                    "sub_param": {
                        "type": "string",
                        "description": "Sub-parameter value (e.g., 'lead-free', 'high-speed', '235C', '2D', 'in-circuit')"
                    }
                },
                "required": ["pos", "sub_param"]
            }
        ),
        types.Tool(
            name="get_current_sequence",
            description="Get the current state of the orchestrator sequence and validation status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="execute_sequence",
            description="Execute the current sequence if it's valid",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_current_pattern_validity",
            description="Check if the current pattern is valid and which pattern it matches",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_valid_patterns",
            description="Get all valid sequence patterns that the orchestrator accepts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool execution"""
    global app_instance
    
    if app_instance is None:
        return [types.TextContent(
            type="text",
            text="Error: Application not initialized"
        )]
    
    try:
        result = ""
        
        if name == "set_block_at_position":
            result = app_instance.set_block_at_position(arguments["pos"], arguments["block_type"])
        
        elif name == "set_sub_param_at_position":
            result = app_instance.set_sub_param_at_position(arguments["pos"], arguments["sub_param"])
        
        elif name == "get_current_sequence":
            result = app_instance.get_current_sequence()
        
        elif name == "execute_sequence":
            result = app_instance.post_execute_sequence()
        
        elif name == "get_current_pattern_validity":
            result = app_instance.get_current_pattern_validity()
        
        elif name == "get_valid_patterns":
            patterns = app_instance.get_valid_patterns()
            result = "Valid Patterns:\n"
            for idx, pattern in enumerate(patterns, 1):
                result += f"\nPattern {idx}:\n"
                for step_idx, (block, param) in enumerate(pattern, 1):
                    result += f"  Step {step_idx}: {block} ({param})\n"
        
        else:
            result = f"Unknown tool: {name}"
        
        return [types.TextContent(type="text", text=result)]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main entry point for the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="orchestrator",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
