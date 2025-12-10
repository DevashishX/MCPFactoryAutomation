"""
FastMCP Server for PCB Assembly Orchestrator

This server exposes the orchestrator manipulation functions to Claude via FastMCP.
More Pythonic implementation using FastMCP framework.
"""

import threading
import time
from typing import List, Tuple
from mcp.server.fastmcp import FastMCP

# Import the GUI application
from orchestrator_gui import OrchestratorApp

# Global app instance
app_instance = None

# Create FastMCP server
mcp = FastMCP("orchestrator")

def start_gui_thread():
    """Start the GUI in a separate thread"""
    global app_instance
    app_instance = OrchestratorApp()
    app_instance.run()

# Start GUI in background thread
gui_thread = threading.Thread(target=start_gui_thread, daemon=True)
gui_thread.start()
time.sleep(1)  # Wait for app to initialize

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
                    'Soldering', 'Optical Inspection', 'Functional Testing'
    
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
                  - Functional Testing: 'in-circuit', 'functional', 'boundary-scan'
    
    Returns:
        Status message with current sequence
    """
    app = ensure_app()
    return app.set_sub_param_at_position(pos, sub_param)

@mcp.tool()
def get_current_sequence() -> str:
    """
    Get the current state of the orchestrator sequence.
    
    Returns:
        Current sequence with all blocks and parameters, plus validation status
    """
    app = ensure_app()
    return app.get_current_sequence()

@mcp.tool()
def execute_sequence() -> str:
    """
    Execute the current sequence if it's valid.
    
    Returns:
        Execution status message indicating success or failure
    """
    app = ensure_app()
    return app.post_execute_sequence()

@mcp.tool()
def get_current_pattern_validity() -> str:
    """
    Check if the current pattern is valid.
    
    Returns:
        Validation status and which pattern it matches (if valid)
    """
    app = ensure_app()
    return app.get_current_pattern_validity()

@mcp.tool()
def get_valid_patterns() -> str:
    """
    Get all valid sequence patterns that the orchestrator accepts.
    
    Returns:
        Formatted string listing all 3 valid patterns with their steps
    """
    app = ensure_app()
    patterns = app.get_valid_patterns()
    
    result_lines = ["Valid Patterns:\n"]
    
    for pattern_idx, pattern in enumerate(patterns, 1):
        result_lines.append(f"\nPattern {pattern_idx}:")
        for step_idx, (block, param) in enumerate(pattern, 1):
            result_lines.append(f"  Step {step_idx}: {block} ({param})")
    
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

@mcp.tool()
def set_pattern(pattern_number: int) -> str:
    """
    Set the orchestrator to a specific valid pattern.
    
    Args:
        pattern_number: Pattern number (1, 2, or 3)
    
    Returns:
        Status message indicating the pattern was set
    """
    app = ensure_app()
    
    if not 1 <= pattern_number <= len(app.valid_patterns):
        return f"Invalid pattern number. Must be between 1 and {len(app.valid_patterns)}"
    
    pattern = app.valid_patterns[pattern_number - 1]
    
    # Set each block and parameter according to the pattern
    for pos, (block, param) in enumerate(pattern):
        app.blocks[pos] = block
        app.sub_params[pos] = param
    
    app.update_display()
    
    return f"Set to Pattern {pattern_number}: {list(zip(app.blocks, app.sub_params))}"

if __name__ == "__main__":
    mcp.run()
