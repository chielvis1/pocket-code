"""Command executor for interacting with the host terminal."""

import os
import logging
from typing import Dict, Any, Tuple, Optional, List
from .terminal_controller import TerminalController

logger = logging.getLogger('ShellAgent')

class CommandExecutor:
    """Utility for executing commands on the host terminal."""
    
    def __init__(self):
        """Initialize the command executor."""
        self.terminal = TerminalController()
        self.interactive_processes = {}
        logger.info("CommandExecutor initialized with direct terminal control")
    
    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[str, int]:
        """Execute a command on the host terminal.
        
        Args:
            command: The command to execute
            timeout: Optional timeout in seconds
            
        Returns:
            Tuple of (output, return_code)
        """
        logger.info(f"Executing command: {command}")
        return self.terminal.execute_command(command, timeout)
    
    def start_interactive_process(self, command: str) -> str:
        """Start an interactive process.
        
        Args:
            command: The command to start the interactive process
            
        Returns:
            Process ID for future interaction
        """
        logger.info(f"Starting interactive process: {command}")
        return self.terminal.start_interactive_process(command)
    
    def send_to_process(self, process_id: str, input_text: str, 
                        expect_pattern: Optional[str] = None, 
                        timeout: Optional[int] = None) -> str:
        """Send input to an interactive process.
        
        Args:
            process_id: The ID of the process to send input to
            input_text: The text to send
            expect_pattern: Optional pattern to wait for after sending input
            timeout: Optional timeout in seconds
            
        Returns:
            Output received after sending input
        """
        logger.info(f"Sending to process {process_id}: {input_text}")
        return self.terminal.send_to_process(process_id, input_text, expect_pattern, timeout)
    
    def get_process_output(self, process_id: str, timeout: Optional[int] = None) -> str:
        """Get current output from an interactive process.
        
        Args:
            process_id: The ID of the process to get output from
            timeout: How long to wait for output in seconds
            
        Returns:
            Current output from the process
        """
        return self.terminal.get_process_output(process_id, timeout)
    
    def terminate_process(self, process_id: str) -> str:
        """Terminate an interactive process.
        
        Args:
            process_id: The ID of the process to terminate
            
        Returns:
            Result of the termination attempt
        """
        logger.info(f"Terminating process: {process_id}")
        return self.terminal.terminate_process(process_id)
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get command execution history.
        
        Args:
            limit: Optional limit on number of history items to return
            
        Returns:
            List of command history items
        """
        return self.terminal.get_command_history(limit)
    
    def get_current_directory(self) -> str:
        """Get the current working directory.
        
        Returns:
            Current working directory
        """
        return self.terminal.get_current_directory()
    
    def change_directory(self, directory: str) -> Tuple[str, int]:
        """Change the current working directory.
        
        Args:
            directory: Directory to change to
            
        Returns:
            Tuple of (output, return_code)
        """
        logger.info(f"Changing directory to: {directory}")
        return self.terminal.change_directory(directory)
    
    def close(self):
        """Close the terminal and all interactive processes."""
        logger.info("Closing command executor")
        self.terminal.close()
