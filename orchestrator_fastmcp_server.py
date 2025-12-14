import threading
import time
from typing import List, Tuple
from mcp.server.fastmcp import FastMCP
import argparse

from orchestrator_gui import OrchestratorApp
app_instance = None
mcp = FastMCP("PCB process Orchestrator", host="127.0.0.1", port=8000)

def start_gui_thread():
    """Start the GUI in a separate thread"""
    global app_instance
    app_instance = OrchestratorApp()
    app_instance.run()

def ensure_app() -> OrchestratorApp:
    """Ensure app is initialized and return it"""
    if app_instance is None:
        raise RuntimeError("Application not initialized")
    return app_instance

@mcp.tool()
def set_block_at_position(pos: int, block_type: str) -> str:
    """
    Set a specific block type at a given position.
    
    Args:
        pos: Position (0-4) in the sequence
        block_type: One of: 'Solder Paste Application', 'Component Placement', 
                    'Soldering', 'Optical Inspection', 'Testing'
    
    Returns:
        Status message with current sequence
    """
    app = ensure_app()
    return app.set_block_at_position(pos, block_type)

@mcp.tool()
def set_sub_param_at_position(pos: int, sub_param: str) -> str:
    """
    Set a sub-parameter at a given position.
    
    Args:
        pos: Position (0-4) in the sequence
        sub_param: Sub-parameter value. Valid values depend on the block type:
                  - Solder Paste Application: 'lead-free', 'leaded', 'low-temp'
                  - Component Placement: 'high-speed', 'high-precision', 'flexible'
                  - Soldering: '235C', '245C', '260C'
                  - Optical Inspection: '2D', '3D', 'Automated'
                  - Testing: 'in-circuit', 'functional', 'boundary-scan'
    
    Returns:
        Status message with current sequence
    """
    app = ensure_app()
    return app.set_sub_param_at_position(pos, sub_param)

@mcp.tool()
def get_current_process() -> str:
    """
    Get the current state of the orchestrator process.
    
    Returns:
        Current process with all blocks and parameters, plus validation status
    """
    app = ensure_app()
    return app.get_current_process()

@mcp.tool()
def execute_process() -> str:
    """
    Execute the current process if it's valid.
    
    Returns:
        Execution status message indicating success or failure
    """
    app = ensure_app()
    return app.post_execute_process()

@mcp.tool()
def get_current_process_validity() -> str:
    """
    Check if the current process is valid.
    
    Returns:
        Validation status and which process it matches (if valid)
    """
    app = ensure_app()
    return app.get_current_process_validity()

@mcp.tool()
def get_valid_processes() -> str:
    """
    Get all valid process processs that the orchestrator accepts.
    
    Returns:
        Formatted string listing all 9 valid processs with their steps
    """
    app = ensure_app()
    processes = app.get_valid_processes()
    
    result_lines = ["Valid Processes:\n"]
    
    for process_idx, process in enumerate(processes, 1):
        result_lines.append(f"\nProcess {process_idx}:")
        for step_idx, (block, param) in enumerate(process, 1):
            result_lines.append(f"  Step {step_idx}: {block} ({param})")
    
    return "\n".join(result_lines)

@mcp.tool()
def get_possible_blocks_sub_params() -> str:
    """
    Get all possible block types and their valid sub-parameters.
    
    Returns:
        Formatted string listing all block types and their sub-parameters
    """
    app = ensure_app()
    blocks_sub_params = app.get_possible_blocks_sub_params()
    
    result_lines = ["Possible Blocks and Sub-Parameters:\n"]
    
    for block, params in blocks_sub_params.items():
        result_lines.append(f"{block}: {params}")
    
    return "\n".join(result_lines)

@mcp.tool()
def get_block_sub_params(block_type: str) -> str:
    """
    Get valid sub-parameters for a specific block type.
    
    Args:
        block_type: Block type to query
    
    Returns:
        List of valid sub-parameters for the specified block type
    """
    app = ensure_app()
    
    if block_type not in app.block_sub_params:
        valid_blocks = list(app.block_sub_params.keys())
        return f"Invalid block type. Valid options: {valid_blocks}"
    
    params = app.block_sub_params[block_type]
    return f"Valid sub-parameters for '{block_type}': {params}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PCB Assembly Orchestrator FastMCP Server")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio", "http"], 
                       help="Transport protocol (default: stdio)")
    parser.add_argument("--host", type=str, default="127.0.0.1", 
                       help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, 
                       help="HTTP port (default: 8000)")
    args = parser.parse_args()
    
    print(f"Transport: {args.transport}")
    
    gui_thread = threading.Thread(target=start_gui_thread, daemon=True)
    gui_thread.start()
    time.sleep(1)
        
    if args.transport == "http":
        print(f"Starting HTTP server on {args.host}:{args.port}")
        mcp.run(transport="streamable-http")
    else:
        print("Starting stdio server")
        mcp.run(transport="stdio")
