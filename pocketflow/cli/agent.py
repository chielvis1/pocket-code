"""AI Agent implementation using Anthropic's Claude."""

import os
import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any, Callable
from datetime import datetime

from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel

from .permissions import check_directory_access, request_directory_access, check_sudo_access, request_sudo_access
from ..utils.context_manager import EnhancedContextManager
from ..utils.command_executor import CommandExecutor
from ..utils.task_manager import TaskManager
from ..utils.grounding import ResponseGrounder

console = Console()

class Agent:
    """AI Agent powered by Claude 3.7 Sonnet."""
    
    def __init__(self, api_key: str):
        """Initialize the agent with API key."""
        self.client = Anthropic(api_key=api_key)
        self.context_manager = EnhancedContextManager()
        self.command_executor = CommandExecutor()
        self.task_manager = TaskManager()
        self.response_grounder = ResponseGrounder()
        self.system_prompt = """You are a powerful agentic AI coding assistant, powered by Claude 3.7 Sonnet.
You operate directly in the host terminal to help users with coding and system tasks.

Your capabilities include:
1. Understanding and executing shell commands directly on the host machine
2. Reading, writing, and modifying code files
3. Searching codebases and documentation
4. Providing code suggestions and explanations
5. Debugging and troubleshooting

IMPORTANT GUIDELINES:

1. NEVER create hypothetical examples or hallucinate commands
   - Only work with ACTUAL files and commands on the host system
   - If you're unsure about something, ask for clarification
   - Never pretend to execute commands - only use the provided functions

2. When processing user requests:
   - First create a task list of specific steps to accomplish the goal
   - Execute each step in sequence using the provided functions
   - Verify the results of each step before proceeding
   - If errors occur, troubleshoot and resolve before continuing
   - Provide clear updates on progress throughout

3. For all operations:
   - Use execute_command() for running shell commands
   - Use read_file() for reading files
   - Use write_file() for writing/modifying files
   - Always verify command execution results
   - Maintain context of previous operations

4. Format all responses in markdown and include:
   - The task list you've created
   - The actual commands being executed
   - The results/output of each step
   - Verification of results
   - Next steps or completion status

5. ALWAYS execute tasks directly - never just provide instructions
   - You have direct access to the host terminal
   - You can run any command the user has permission to run
   - You are responsible for completing the entire task

6. NEVER use hypothetical language or create examples
   - Don't use phrases like "for example", "let's say", "imagine", etc.
   - Don't create sample code unless you're actually writing it to a file
   - Don't describe what "would" happen - actually execute and report what DID happen

Remember: You are controlling the ACTUAL host terminal, not a simulation.
Your actions have real effects on the user's system.
"""
    
    def log_progress(self, message: str, style: str = "bold blue"):
        """Log progress message to console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(f"[{timestamp}] [{style}]{message}[/{style}]")
    
    def execute_command(self, command: str) -> Tuple[str, int]:
        """Execute a shell command and return output and status."""
        try:
            # Log command execution
            self.log_progress(f"Executing command: {command}")
            
            # Check if command needs sudo
            needs_sudo = command.startswith("sudo ")
            if needs_sudo and not check_sudo_access():
                if request_sudo_access():
                    self.log_progress("Please run the command again after configuring sudo access", "yellow")
                    return "Operation requires sudo access. Please try again after configuring sudo.", 1
                return "Operation cancelled - sudo access required.", 1
            
            # Check directory access
            cwd = self.command_executor.get_current_directory()
            if not check_directory_access(cwd):
                if request_directory_access(cwd):
                    # User granted access, try again
                    return self.execute_command(command)
                return f"Operation cancelled - no access to directory: {cwd}", 1
            
            # Update task step status if we have an active task
            current_task = self.task_manager.get_current_task()
            if current_task:
                current_step = self.task_manager.get_current_step()
                if current_step and "status" in current_step and current_step["status"] in ["pending", "in_progress"]:
                    step_index = current_task["current_step_index"]
                    self.task_manager.update_step_status(step_index, "in_progress")
            
            # Execute command using the direct terminal controller
            output, return_code = self.command_executor.execute_command(command)
            
            # Update task step status with result
            if current_task:
                current_step = self.task_manager.get_current_step()
                if current_step and "status" in current_step and current_step["status"] == "in_progress":
                    step_index = current_task["current_step_index"]
                    status = "completed" if return_code == 0 else "error"
                    self.task_manager.update_step_status(step_index, status, output)
            
            # Log command result
            if return_code == 0:
                self.log_progress("Command completed successfully", "green")
            else:
                self.log_progress(f"Command failed with exit code {return_code}", "red")
            
            return output, return_code
            
        except Exception as e:
            self.log_progress(f"Error executing command: {str(e)}", "red")
            return str(e), 1
    
    def start_interactive_process(self, command: str) -> str:
        """Start an interactive process and return its ID."""
        try:
            # Log process start
            self.log_progress(f"Starting interactive process: {command}")
            
            # Start the process using the terminal controller
            process_id = self.command_executor.start_interactive_process(command)
            
            return process_id
            
        except Exception as e:
            self.log_progress(f"Error starting interactive process: {str(e)}", "red")
            return f"Error: {str(e)}"
    
    def send_to_process(self, process_id: str, input_text: str, expect_pattern: Optional[str] = None) -> str:
        """Send input to an interactive process."""
        try:
            # Log input sending
            self.log_progress(f"Sending input to process {process_id}")
            
            # Send input using the terminal controller
            output = self.command_executor.send_to_process(process_id, input_text, expect_pattern)
            
            return output
            
        except Exception as e:
            self.log_progress(f"Error sending to process: {str(e)}", "red")
            return f"Error: {str(e)}"
    
    def terminate_process(self, process_id: str) -> str:
        """Terminate an interactive process."""
        try:
            # Log process termination
            self.log_progress(f"Terminating process {process_id}")
            
            # Terminate the process using the terminal controller
            result = self.command_executor.terminate_process(process_id)
            
            return result
            
        except Exception as e:
            self.log_progress(f"Error terminating process: {str(e)}", "red")
            return f"Error: {str(e)}"
    
    def read_file(self, path: str) -> str:
        """Read contents of a file."""
        try:
            # Log file reading
            self.log_progress(f"Reading file: {path}")
            
            # Check directory access
            dir_path = str(Path(path).parent)
            if not check_directory_access(dir_path):
                if request_directory_access(dir_path):
                    # User granted access, try again
                    return self.read_file(path)
                return f"Operation cancelled - no access to directory: {dir_path}"
            
            with open(path, 'r') as f:
                content = f.read()
                self.log_progress(f"Successfully read {len(content)} bytes from {path}", "green")
                return content
        except Exception as e:
            self.log_progress(f"Error reading file: {str(e)}", "red")
            return f"Error reading file: {str(e)}"
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        try:
            # Log file writing
            self.log_progress(f"Writing to file: {path}")
            
            # Check directory access
            dir_path = str(Path(path).parent)
            if not check_directory_access(dir_path):
                if request_directory_access(dir_path):
                    # User granted access, try again
                    return self.write_file(path, content)
                return f"Operation cancelled - no access to directory: {dir_path}"
            
            with open(path, 'w') as f:
                f.write(content)
                self.log_progress(f"Successfully wrote {len(content)} bytes to {path}", "green")
            return f"Successfully wrote to {path}"
        except Exception as e:
            self.log_progress(f"Error writing file: {str(e)}", "red")
            return f"Error writing file: {str(e)}"
    
    def process_request(self, request: str) -> str:
        """Process a user request through Claude."""
        try:
            # Log request processing
            self.log_progress("Processing request...")
            
            # Add user request to context
            self.context_manager.add_message("user", request)
            
            # Get conversation history - use all available history instead of limiting to 5
            conversation_history = self.context_manager.get_conversation_history()
            
            # Create messages
            messages = []
            
            # Add conversation history
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add available functions to the request
            function_context = """
Available functions:
- execute_command(command: str) -> Tuple[str, int]: Execute a shell command and return its actual output
- start_interactive_process(command: str) -> str: Start an interactive process and return its ID
- send_to_process(process_id: str, input_text: str, expect_pattern: Optional[str] = None) -> str: Send input to an interactive process
- terminate_process(process_id: str) -> str: Terminate an interactive process
- read_file(path: str) -> str: Read contents of a file
- write_file(path: str, content: str) -> str: Write content to a file

Current working directory: {cwd}
Sudo access: {sudo}

IMPORTANT REMINDERS:
1. You are controlling the ACTUAL host terminal, not a simulation
2. Create a task list for each request and execute each step
3. Verify results after each step and handle errors
4. NEVER hallucinate or create hypothetical examples
5. Only work with ACTUAL files and commands on the host system
""".format(
                cwd=self.command_executor.get_current_directory(),
                sudo="available" if check_sudo_access() else "not configured"
            )
            
            # Get context summary if available
            context_summary = self.context_manager.context_summary
            if context_summary:
                function_context += f"\nCONVERSATION SUMMARY:\n{context_summary}\n"
            
            # Add current task information if available
            current_task = self.task_manager.get_current_task()
            if current_task and current_task.get("steps"):
                task_list = self.task_manager.format_task_list()
                function_context += f"\nCURRENT TASK STATUS:\n{task_list}\n"
            
            # Get response from Claude with system prompt as parameter
            self.log_progress("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=messages,
                system=self.system_prompt,
                temperature=0.7
            )
            
            # Get the response text
            response_text = response.content[0].text
            
            # Extract task steps if this is a new request
            if not current_task or current_task.get("status") == "completed":
                task_steps = self.response_grounder.extract_task_steps(response_text)
                if task_steps and len(task_steps) >= 2:
                    self.task_manager.create_task(request, task_steps)
                    self.log_progress(f"Created task with {len(task_steps)} steps")
            
            # Ground the response to prevent hallucinations
            grounded_response, verification_results = self.response_grounder.ground_response(response_text)
            
            # Add response to context
            self.context_manager.add_message("assistant", grounded_response)
            
            # Process commands in the response
            processed_response = self._process_commands_in_response(grounded_response)
            
            # Generate a new summary periodically (every 10 messages)
            if len(conversation_history) % 10 == 0:
                self._generate_summary()
            
            return processed_response
            
        except Exception as e:
            self.log_progress(f"Error processing request: {str(e)}", "red")
            return f"Error: {str(e)}"
    
    def _process_commands_in_response(self, response_text: str) -> str:
        """Process and execute commands found in the response."""
        # Check if the response contains commands to execute
        if "execute_command(" in response_text:
            # Extract all commands from the response
            commands = []
            pos = 0
            while True:
                start = response_text.find('execute_command("', pos)
                if start == -1:
                    break
                start += len('execute_command("')
                end = response_text.find('")', start)
                if end == -1:
                    break
                commands.append(response_text[start:end])
                pos = end + 2
            
            # Execute each command and update the response
            for command in commands:
                # Execute the command
                output, status = self.execute_command(command)
                
                # Replace the function call with the actual output
                placeholder = f'execute_command("{command}")'
                replacement = f'```shell\n$ {command}\n{output}\n```'
                response_text = response_text.replace(placeholder, replacement)
        
        # Process interactive process operations
        if "start_interactive_process(" in response_text:
            # Extract all process start commands
            process_starts = []
            pos = 0
            while True:
                start = response_text.find('start_interactive_process("', pos)
                if start == -1:
                    break
                start += len('start_interactive_process("')
                end = response_text.find('")', start)
                if end == -1:
                    break
                process_starts.append(response_text[start:end])
                pos = end + 2
            
            # Start each process and update the response
            for command in process_starts:
                # Start the process
                process_id = self.start_interactive_process(command)
                
                # Replace the function call with the actual process ID
                placeholder = f'start_interactive_process("{command}")'
                replacement = f'Process started: {process_id}\nCommand: {command}'
                response_text = response_text.replace(placeholder, replacement)
        
        # Process send_to_process operations
        if "send_to_process(" in response_text:
            # This is more complex due to multiple parameters
            # We'll use a simplified approach that might not catch all cases
            pos = 0
            while True:
                start = response_text.find('send_to_process(', pos)
                if start == -1:
                    break
                
                # Find the closing parenthesis, accounting for nested parentheses
                paren_count = 1
                end = start + len('send_to_process(')
                while paren_count > 0 and end < len(response_text) - 1:
                    end += 1
                    if response_text[end] == '(':
                        paren_count += 1
                    elif response_text[end] == ')':
                        paren_count -= 1
                
                if paren_count > 0:
                    break  # Unmatched parentheses
                
                # Extract the full function call
                func_call = response_text[start:end+1]
                
                # Try to parse parameters (this is a simplified approach)
                try:
                    # Extract process_id
                    pid_start = func_call.find('"', func_call.find('(')) + 1
                    pid_end = func_call.find('"', pid_start)
                    process_id = func_call[pid_start:pid_end]
                    
                    # Extract input_text
                    input_start = func_call.find('"', pid_end + 1) + 1
                    input_end = func_call.find('"', input_start)
                    input_text = func_call[input_start:input_end]
                    
                    # Send to the process
                    output = self.send_to_process(process_id, input_text)
                    
                    # Replace the function call with the actual output
                    replacement = f'Sent to process {process_id}: "{input_text}"\nOutput: {output}'
                    response_text = response_text.replace(func_call, replacement)
                except:
                    # If parsing fails, just move on
                    pass
                
                pos = end + 1
        
        # Process terminate_process operations
        if "terminate_process(" in response_text:
            # Extract all process termination commands
            process_terms = []
            pos = 0
            while True:
                start = response_text.find('terminate_process("', pos)
                if start == -1:
                    break
                start += len('terminate_process("')
                end = response_text.find('")', start)
                if end == -1:
                    break
                process_terms.append(response_text[start:end])
                pos = end + 2
            
            # Terminate each process and update the response
            for process_id in process_terms:
                # Terminate the process
                result = self.terminate_process(process_id)
                
                # Replace the function call with the actual result
                placeholder = f'terminate_process("{process_id}")'
                replacement = f'Process terminated: {process_id}\nResult: {result}'
                response_text = response_text.replace(placeholder, replacement)
        
        # Process read_file calls
        if "read_file(" in response_text:
            # Extract all file paths from the response
            file_paths = []
            pos = 0
            while True:
                start = response_text.find('read_file("', pos)
                if start == -1:
                    break
                start += len('read_file("')
                end = response_text.find('")', start)
                if end == -1:
                    break
                file_paths.append(response_text[start:end])
                pos = end + 2
            
            # Read each file and update the response
            for file_path in file_paths:
                # Read the file
                content = self.read_file(file_path)
                
                # Replace the function call with the actual content
                placeholder = f'read_file("{file_path}")'
                
                # Format based on file type
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.py', '.js', '.java', '.c', '.cpp', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.ts']:
                    replacement = f'```{ext[1:]}\n{content}\n```'
                elif ext in ['.json', '.xml', '.yaml', '.yml', '.toml']:
                    replacement = f'```{ext[1:]}\n{content}\n```'
                elif ext in ['.md', '.markdown']:
                    replacement = f'```markdown\n{content}\n```'
                elif ext in ['.txt', '.log', '.csv']:
                    replacement = f'```\n{content}\n```'
                else:
                    replacement = f'```\n{content}\n```'
                
                response_text = response_text.replace(placeholder, replacement)
        
        # Process write_file calls
        if "write_file(" in response_text:
            # Extract all write operations from the response
            write_ops = []
            pos = 0
            while True:
                start = response_text.find('write_file("', pos)
                if start == -1:
                    break
                
                # Extract file path
                path_start = start + len('write_file("')
                path_end = response_text.find('",', path_start)
                if path_end == -1:
                    break
                
                # Extract content (this is more complex due to potential escaping)
                content_start = path_end + 2
                # Find the closing parenthesis, accounting for nested parentheses
                paren_count = 1
                content_end = content_start
                while paren_count > 0 and content_end < len(response_text) - 1:
                    content_end += 1
                    if response_text[content_end] == '(' and response_text[content_end-1] != '\\':
                        paren_count += 1
                    elif response_text[content_end] == ')' and response_text[content_end-1] != '\\':
                        paren_count -= 1
                
                if paren_count > 0:
                    break  # Unmatched parentheses
                
                # Extract the path and content
                file_path = response_text[path_start:path_end]
                content = response_text[content_start:content_end].strip()
                
                # Clean up the content (remove quotes and handle escaping)
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                
                write_ops.append((file_path, content))
                pos = content_end + 1
            
            # Process each write operation
            for file_path, content in write_ops:
                # Write to the file
                result = self.write_file(file_path, content)
                
                # Replace the function call with the result
                placeholder = f'write_file("{file_path}", "{content}")'
                replacement = f'File written: {file_path}\nResult: {result}'
                response_text = response_text.replace(placeholder, replacement)
        
        return response_text
    
    def _generate_summary(self):
        """Generate a summary of the current conversation."""
        self.log_progress("Generating conversation summary...")
        
        # Define a function to use Claude for summarization
        def summarize_with_claude(prompt: str) -> str:
            try:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.content[0].text
            except Exception as e:
                self.log_progress(f"Error generating summary: {str(e)}", "red")
                return "Failed to generate summary."
        
        # Generate summary using the context manager
        summary = self.context_manager.generate_summary(summarize_with_claude)
        self.log_progress(f"Summary generated: {summary[:50]}...", "green")
        
        return summary
    
    def end_session(self):
        """End the current session."""
        self.context_manager.end_session()
        self.command_executor.close()
        self.log_progress("Session ended", "yellow")
        
        # Complete any active task
        current_task = self.task_manager.get_current_task()
        if current_task and current_task.get("status") != "completed":
            self.task_manager.complete_task("Session ended before task completion")
