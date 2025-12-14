import customtkinter as ctk
from processes import VALID_PROCESSES
from typing import List, Tuple

class OrchestratorApp:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("PCB Assembly Orchestrator")
        self.root.geometry("900x1200")
        
        self.blocks = ['Solder Paste Application', 'Component Placement', 'Soldering', 'Optical Inspection', 'Testing'] # correspond sequentially to color_map
        self.sub_params = ['lead-free', 'high-speed', '235C', '2D', 'in-circuit']  # Sub-parameters for each block
        
        self.block_sub_params = {
            'Solder Paste Application': ['lead-free', 'leaded', 'low-temp'],
            'Component Placement': ['high-speed', 'high-precision', 'flexible'],
            'Soldering': ['235C', '245C', '260C'],
            'Optical Inspection': ['2D', '3D', 'Automated'],
            'Testing': ['in-circuit', 'functional', 'boundary-scan']
        }
        
        self.valid_processes = VALID_PROCESSES
        
        self.color_map = {
            'Solder Paste Application': '#3b82f6',  # blue
            'Component Placement': "#84f1ed",  # teal
            'Soldering': '#eab308',  # yellow
            'Optical Inspection': '#a855f7',  # purple
            'Testing': '#22c55e'   # green
        }
        
        self.block_labels = []
        self.sub_param_labels = []
        self.dropdowns = []
        self.sub_param_dropdowns = []
        self.status_label = None
        self.execute_button = None
        self.execution_status_label = None
        
        self._setup_gui()
        self.update_display()
        
    def _setup_gui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        title = ctk.CTkLabel(main_frame, text="Orchestrator for PCB Assembly", 
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0, 20))
        
        # Block display frame
        block_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        block_frame.pack(pady=20)
        
        # Create 5 blocks with arrows and sub-parameters
        for i in range(5):
            # Container for block and sub-parameter
            block_container = ctk.CTkFrame(block_frame, fg_color="transparent")
            block_container.grid(row=1, column=i*2, padx=5)
            
            # Step label above block
            step_label = ctk.CTkLabel(block_frame, text=f"Step {i+1}",
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     text_color="black")
            step_label.grid(row=0, column=i*2, pady=(0, 10))
            
            # Block - split text into multiple lines
            block_text = self.blocks[i].replace(' ', '\n')
            block = ctk.CTkLabel(block_container, 
                                text=block_text,
                               width=100, height=100,
                               font=ctk.CTkFont(size=16, weight="bold"),
                               corner_radius=10,
                               justify="center")
            block.pack()
            self.block_labels.append(block)
            
            # Sub-parameter label
            sub_param = ctk.CTkLabel(block_container, text=self.sub_params[i],
                                    font=ctk.CTkFont(size=16, weight="bold"),
                                    text_color="black")
            sub_param.pack(pady=(5, 0))
            self.sub_param_labels.append(sub_param)
            
            # Arrow (except after last block)
            if i < 4:
                arrow = ctk.CTkLabel(block_frame, text="→",
                                   font=ctk.CTkFont(size=32),
                                   text_color="black")
                arrow.grid(row=1, column=i*2+1, padx=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="Status: Waiting for sequence...",
                                        font=ctk.CTkFont(size=16),
                                        text_color="gray")
        self.status_label.pack(pady=20)
        
        # Execute button
        self.execute_button = ctk.CTkButton(main_frame, text="Execute",
                                           font=ctk.CTkFont(size=16, weight="bold"),
                                           command=self.execute,
                                           state="disabled",
                                           width=200, height=40)
        self.execute_button.pack(pady=10)
        
        # Execution status label
        self.execution_status_label = ctk.CTkLabel(main_frame, text="",
                                                   font=ctk.CTkFont(size=14),
                                                   text_color="gray")
        self.execution_status_label.pack(pady=5)
        
        # Control frame with dropdowns
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(pady=10)
        
        # Create 5 dropdown combos for setting blocks
        for i in range(5):
            # Container for each control
            control_container = ctk.CTkFrame(control_frame, fg_color="transparent")
            control_container.grid(row=0, column=i, padx=10, pady=5)
            
            # Label
            label = ctk.CTkLabel(control_container, text=f"Step {i+1}:",
                               font=ctk.CTkFont(size=12))
            label.pack()
            
            # Dropdown for block type
            dropdown = ctk.CTkComboBox(control_container, 
                                      values=['Solder Paste Application', 'Component Placement', 'Soldering', 'Optical Inspection', 'Testing'],
                                      width=120,
                                      command=lambda value, pos=i: self.set_block_at_position(pos, value))
            dropdown.set(self.blocks[i])
            dropdown.pack(pady=5)
            self.dropdowns.append(dropdown)
            
            # Label for sub-parameter
            sub_label = ctk.CTkLabel(control_container, text="Parameter",
                                    font=ctk.CTkFont(size=12))
            sub_label.pack(pady=(5, 0))
            
            # Dropdown for sub-parameter - initially populated based on block type
            sub_dropdown = ctk.CTkComboBox(control_container,
                                          values=self.block_sub_params[self.blocks[i]],
                                          width=120,
                                          command=lambda value, pos=i: self.set_sub_param_at_position(pos, value))
            sub_dropdown.set(self.sub_params[i])
            sub_dropdown.pack(pady=5)
            self.sub_param_dropdowns.append(sub_dropdown)
        
        # Valid sequences display section
        sequences_frame = ctk.CTkFrame(main_frame)
        sequences_frame.pack(pady=20, padx=10, fill="both", expand=True)
        
        sequences_title = ctk.CTkLabel(sequences_frame, text="Valid Sequences:",
                                      font=ctk.CTkFont(size=16, weight="bold"))
        sequences_title.pack(pady=(10, 5))
        
        # Create text box to display valid sequences
        self.sequences_textbox = ctk.CTkTextbox(sequences_frame, 
                                               height=150,
                                               font=ctk.CTkFont(size=12),
                                               wrap="word")
        self.sequences_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Populate valid sequences
        self._populate_valid_processes()
    
    def _populate_valid_processes(self):
        """Populate the textbox with valid sequence processs"""
        self.sequences_textbox.delete("1.0", "end")
        # for process_idx, process in enumerate(self.valid_processes, 1):
        #     sequence_text = f"Process {process_idx}:\n"
        #     for step_idx, (block, param) in enumerate(process, 1):
        #         sequence_text += f"  Step {step_idx}: {block} ({param})\n"
        #     sequence_text += "\n"
        #     self.sequences_textbox.insert("end", sequence_text)
        with open("D:/MCPFactoryAutomation/documents/all_processes_overview.txt", "r") as f:
            content = f.read()
            content = content.replace("*", "")
            
            self.sequences_textbox.insert("end", content)
        self.sequences_textbox.configure(state="disabled")
        
    def update_display(self):
        """Update the visual display of blocks"""
        for i, label in enumerate(self.block_labels):
            block_type = self.blocks[i]
            block_color = self.color_map[block_type]
            # Split block name into multiple lines for display
            block_text = block_type.replace(' ', '\n')
            label.configure(text=block_text, fg_color=block_color)
        
        # Update sub-parameter labels
        for i, sub_label in enumerate(self.sub_param_labels):
            sub_label.configure(text=self.sub_params[i])
        
        # Update dropdowns to match current blocks
        for i, dropdown in enumerate(self.dropdowns):
            dropdown.set(self.blocks[i])
        
        # Update sub-parameter dropdowns with valid options for each block
        for i, sub_dropdown in enumerate(self.sub_param_dropdowns):
            block_type = self.blocks[i]
            valid_sub_params = self.block_sub_params[block_type]
            sub_dropdown.configure(values=valid_sub_params)
            
            # Reset to first valid sub-param if current is invalid for this block
            if self.sub_params[i] not in valid_sub_params:
                self.sub_params[i] = valid_sub_params[0]
            
            sub_dropdown.set(self.sub_params[i])
        
        # Clear execution status when sequence changes
        self.execution_status_label.configure(text="", text_color="gray")
        
        self.check_process()
        
    def check_process(self) -> str:
        """Check if current sequence matches any of the valid processs"""
        # Create current sequence as list of tuples
        current_sequence = [(self.blocks[i], self.sub_params[i]) for i in range(5)]
        
        # Check if current sequence matches any valid process
        for process_idx, process in enumerate(self.valid_processes, 1):
            if current_sequence == process:
                self.status_label.configure(
                    text=f"✓ Valid Combination! (Process {process_idx})",
                    text_color="#05b044"
                )
                self.execute_button.configure(state="normal")
                return f"Valid Combination (Process {process_idx})"
        
        self.status_label.configure(text="Status: Invalid sequence",
                                   text_color="gray")
        self.execute_button.configure(state="disabled")
        return "Invalid sequence"
    
    def execute(self) -> str:
        """Execute the current valid sequence"""
        current_sequence = [(self.blocks[i], self.sub_params[i]) for i in range(5)]
        
        # Check if sequence matches any valid process
        for process_idx, process in enumerate(self.valid_processes, 1):
            if current_sequence == process:
                self.execution_status_label.configure(
                    text=f"✓ Sequence Executed Successfully! (Process {process_idx})",
                    text_color="#22c55e"
                )
                return f"Executed sequence: {current_sequence} (Process {process_idx})"
        
        self.execution_status_label.configure(
            text="✗ Cannot execute invalid sequence",
            text_color="#f30a0a"
        )
        return "Cannot execute invalid sequence"
    
    # # # # # # # # # # # # # # # # # # # #
    # Methods for MCP integration # # # # #
    # # # # # # # # # # # # # # # # # # # #
       
    def set_block_at_position(self, pos: int, block_type: str) -> str:
        """Set a specific block type at a position"""
        if 0 <= pos < 5 and block_type in ['Solder Paste Application', 'Component Placement', 'Soldering', 'Optical Inspection', 'Testing']:
        # if 0 <= pos < 5 and block_type in self.blocks_sub_params.keys():            
            self.blocks[pos] = block_type
            self.sub_params[pos] = self.block_sub_params[block_type][0]
            self.update_display()
            return f"Set position {pos} to {block_type}. Current: {list(zip(self.blocks, self.sub_params))}"
        return "Invalid position or block type"
    
    def set_sub_param_at_position(self, pos: int, sub_param: str) -> str:
        """Set a sub-parameter at a position"""
        if 0 <= pos < 5:
            block_type = self.blocks[pos]
            valid_sub_params = self.block_sub_params[block_type]
            
            if sub_param in valid_sub_params:
                self.sub_params[pos] = sub_param
                self.update_display()
                return f"Set sub-parameter at position {pos} to {sub_param}. Current: {list(zip(self.blocks, self.sub_params))}"
            return f"Invalid sub-parameter '{sub_param}' for block type '{block_type}'. Valid options: {valid_sub_params}"
        return "Invalid position"
    
    def get_possible_blocks_sub_params(self) -> dict:
        """Return available blocks and their sub-parameters"""
        return self.block_sub_params
    
    def get_current_process(self) -> str:
        status = self.check_process()
        current_sequence = list(zip(self.blocks, self.sub_params))
        return f"Current process: {current_sequence}. Status: {status}"
    
    def post_execute_process(self) -> str:
        """execute the current process via MCP"""
        return self.execute()
    
    def get_current_process_validity(self) -> str:
        """Return whether the current process is valid or not"""
        return self.check_process()
    
    def get_valid_processes(self) -> List[List[Tuple[str, str]]]:
        """Return the list of valid processes"""
        return self.valid_processes
    
    # End of MCP integration methods #
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = OrchestratorApp()
    app.run()