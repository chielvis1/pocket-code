"""Direct terminal controller for interacting with the host terminal."""

import os
import sys
import time
import signal
import logging
import pexpect
from typing import Optional, Tuple, List, Dict, Any, Callable

logger = logging.getLogger('ShellAgent')

class TerminalController:
    """Controller for direct interaction with the host terminal."""
    
    def __init__(self, shell: str = "/bin/bash", timeout: int = 30):
        """Initialize the terminal controller.
        
        Args:
            shell: The shell to use (default: /bin/bash)
            timeout: Default timeout for commands in seconds
        """
        self.shell = shell
        self.timeout = timeout
        self.process = None
        self.cwd = os.getcwd()
        self.env = dict(os.environ)
        self.command_history = []
        self.last_output = ""
        self.interactive_processes = {}
        self._initialize_terminal()
        
    def _initialize_terminal(self):
        """Initialize the terminal process."""
        try:
            # Spawn the shell process
            self.process = pexpect.spawn(
                self.shell,
                encoding='utf-8',
                echo=False,
                timeout=self.timeout
            )
            
            # Set up terminal size
            self.process.setwinsize(24, 80)
            
            # Wait for prompt
            self.process.expect([r'[$#>] $', pexpect.EOF, pexpect.TIMEOUT])
            
            # Set environment variables for better interaction
            self._setup_environment()
            
            logger.info(f"Terminal initialized with shell: {self.shell}")
            return True
        except Exception as e:
            logger.error(f"Error initializing terminal: {str(e)}")
            return False
    
    def _setup_environment(self):
        """Set up environment variables for better interaction."""
        # Set PS1 to a simple, consistent prompt that's easy to detect
        self.execute_command("export PS1='$ '")
        
        # Disable command history expansion
        self.execute_command("set +H")
        
        # Disable line editing to prevent issues with complex commands
        self.execute_command("set +o vi")
        self.execute_command("set +o emacs")
        
        # Update current working directory
        output, _ = self.execute_command("pwd")
        if output.strip():
            self.cwd = output.strip()
    
    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[str, int]:
        """Execute a command in the terminal and return output and status.
        
        Args:
            command: The command to execute
            timeout: Command-specific timeout in seconds
            
        Returns:
            Tuple of (output, return_code)
        """
        if not self.process or not self.process.isalive():
            logger.warning("Terminal process not alive, reinitializing")
            if not self._initialize_terminal():
                return "Failed to initialize terminal", 1
        
        try:
            # Use command-specific timeout or default
            cmd_timeout = timeout if timeout is not None else self.timeout
            
            # Send the command
            self.process.sendline(command)
            
            # Wait for command to complete and prompt to return
            patterns = [r'[$#>] $', pexpect.EOF, pexpect.TIMEOUT]
            index = self.process.expect(patterns, timeout=cmd_timeout)
            
            # Get the output (excluding the command and the prompt)
            output = self.process.before
            
            # Clean up the output
            if output.startswith(command):
                output = output[len(command):].lstrip('\r\n')
            
            # Get the return code
            self.process.sendline("echo $?")
            self.process.expect(patterns, timeout=5)
            return_code_str = self.process.before.strip()
            
            # Extract just the return code number
            if return_code_str.startswith("echo $?"):
                return_code_str = return_code_str[len("echo $?"):].strip()
            
            try:
                return_code = int(return_code_str)
            except ValueError:
                logger.warning(f"Could not parse return code: {return_code_str}")
                return_code = 1 if index > 0 else 0
            
            # Update command history
            self.command_history.append({
                "command": command,
                "output": output,
                "return_code": return_code,
                "timestamp": time.time()
            })
            
            # Update last output
            self.last_output = output
            
            # Update current working directory if cd command
            if command.strip().startswith("cd "):
                output_pwd, _ = self.execute_command("pwd")
                if output_pwd.strip():
                    self.cwd = output_pwd.strip()
            
            return output, return_code
            
        except pexpect.TIMEOUT:
            logger.error(f"Command timed out after {cmd_timeout} seconds: {command}")
            return f"Command timed out after {cmd_timeout} seconds", 124
            
        except pexpect.EOF:
            logger.error(f"Terminal process ended unexpectedly during command: {command}")
            return "Terminal process ended unexpectedly", 1
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return str(e), 1
    
    def start_interactive_process(self, command: str) -> str:
        """Start an interactive process and return its ID.
        
        Args:
            command: The command to start the interactive process
            
        Returns:
            Process ID for future interaction
        """
        try:
            # Generate a unique ID for this process
            process_id = f"proc_{int(time.time())}"
            
            # Spawn the process
            process = pexpect.spawn(
                command,
                encoding='utf-8',
                echo=False,
                timeout=self.timeout,
                cwd=self.cwd
            )
            
            # Set up terminal size
            process.setwinsize(24, 80)
            
            # Store the process
            self.interactive_processes[process_id] = {
                "process": process,
                "command": command,
                "start_time": time.time(),
                "last_output": ""
            }
            
            # Wait a moment for initial output
            time.sleep(0.5)
            
            # Get initial output if available
            output = ""
            if process.isalive():
                try:
                    # Try to read any available output without blocking
                    process.expect([pexpect.TIMEOUT], timeout=1)
                    output = process.before + process.after
                except:
                    pass
                
                self.interactive_processes[process_id]["last_output"] = output
            
            logger.info(f"Started interactive process {process_id}: {command}")
            return process_id
            
        except Exception as e:
            logger.error(f"Error starting interactive process: {str(e)}")
            return f"Error: {str(e)}"
    
    def send_to_process(self, process_id: str, input_text: str, expect_pattern: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """Send input to an interactive process.
        
        Args:
            process_id: The ID of the process to send input to
            input_text: The text to send
            expect_pattern: Optional pattern to wait for after sending input
            timeout: Command-specific timeout in seconds
            
        Returns:
            Output received after sending input
        """
        if process_id not in self.interactive_processes:
            return f"Error: Process {process_id} not found"
        
        process_info = self.interactive_processes[process_id]
        process = process_info["process"]
        
        if not process.isalive():
            return f"Error: Process {process_id} is no longer running"
        
        try:
            # Use command-specific timeout or default
            cmd_timeout = timeout if timeout is not None else self.timeout
            
            # Send the input
            process.sendline(input_text)
            
            # Wait for expected pattern or timeout
            if expect_pattern:
                index = process.expect([expect_pattern, pexpect.EOF, pexpect.TIMEOUT], timeout=cmd_timeout)
            else:
                # If no pattern specified, just wait a moment for output
                time.sleep(0.5)
                index = process.expect([pexpect.TIMEOUT], timeout=1)
            
            # Get the output
            output = process.before
            if index == 0 and expect_pattern:
                output += process.after
            
            # Update last output
            process_info["last_output"] = output
            
            return output
            
        except pexpect.TIMEOUT:
            logger.warning(f"Timeout waiting for response from process {process_id}")
            return "Timeout waiting for response"
            
        except pexpect.EOF:
            logger.warning(f"Process {process_id} ended")
            return "Process ended"
            
        except Exception as e:
            logger.error(f"Error sending to process: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_process_output(self, process_id: str, timeout: Optional[int] = None) -> str:
        """Get current output from an interactive process without sending input.
        
        Args:
            process_id: The ID of the process to get output from
            timeout: How long to wait for output in seconds
            
        Returns:
            Current output from the process
        """
        if process_id not in self.interactive_processes:
            return f"Error: Process {process_id} not found"
        
        process_info = self.interactive_processes[process_id]
        process = process_info["process"]
        
        if not process.isalive():
            return f"Process {process_id} is no longer running. Last output:\n{process_info['last_output']}"
        
        try:
            # Use command-specific timeout or default
            cmd_timeout = timeout if timeout is not None else 1  # Short timeout for non-blocking check
            
            # Try to read any available output without blocking
            process.expect([pexpect.TIMEOUT], timeout=cmd_timeout)
            output = process.before + process.after
            
            # Update last output if we got something new
            if output:
                process_info["last_output"] = output
            
            return output if output else process_info["last_output"]
            
        except Exception as e:
            logger.error(f"Error getting process output: {str(e)}")
            return f"Error: {str(e)}"
    
    def terminate_process(self, process_id: str) -> str:
        """Terminate an interactive process.
        
        Args:
            process_id: The ID of the process to terminate
            
        Returns:
            Result of the termination attempt
        """
        if process_id not in self.interactive_processes:
            return f"Error: Process {process_id} not found"
        
        process_info = self.interactive_processes[process_id]
        process = process_info["process"]
        
        if not process.isalive():
            self.interactive_processes.pop(process_id)
            return f"Process {process_id} was already terminated"
        
        try:
            # Try graceful termination first
            process.sendcontrol('c')
            time.sleep(0.5)
            
            # If still alive, try SIGTERM
            if process.isalive():
                process.kill(signal.SIGTERM)
                time.sleep(0.5)
            
            # If still alive, force kill
            if process.isalive():
                process.kill(signal.SIGKILL)
            
            # Clean up
            self.interactive_processes.pop(process_id)
            
            return f"Process {process_id} terminated"
            
        except Exception as e:
            logger.error(f"Error terminating process: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get command execution history.
        
        Args:
            limit: Optional limit on number of history items to return
            
        Returns:
            List of command history items
        """
        if limit is not None and limit > 0:
            return self.command_history[-limit:]
        return self.command_history
    
    def get_current_directory(self) -> str:
        """Get the current working directory.
        
        Returns:
            Current working directory
        """
        return self.cwd
    
    def change_directory(self, directory: str) -> Tuple[str, int]:
        """Change the current working directory.
        
        Args:
            directory: Directory to change to
            
        Returns:
            Tuple of (output, return_code)
        """
        return self.execute_command(f"cd {directory}")
    
    def close(self):
        """Close the terminal and all interactive processes."""
        # Terminate all interactive processes
        for process_id in list(self.interactive_processes.keys()):
            self.terminate_process(process_id)
        
        # Close the main terminal process
        if self.process and self.process.isalive():
            self.process.sendline("exit")
            self.process.close()
        
        logger.info("Terminal controller closed")
