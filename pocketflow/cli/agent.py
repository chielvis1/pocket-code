"""AI Agent implementation using Anthropic's Claude."""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel

from .permissions import check_directory_access, request_directory_access, check_sudo_access, request_sudo_access

console = Console()

class Agent:
    """AI Agent powered by Claude 3.7 Sonnet."""
    
    def __init__(self, api_key: str):
        """Initialize the agent with API key."""
        self.client = Anthropic(api_key=api_key)
        self.conversation_history: List[Dict] = []
        self.system_prompt = """You are a powerful agentic AI coding assistant, powered by Claude 3.7 Sonnet.
You operate in a command-line interface to help users with coding tasks.

Your capabilities include:
1. Understanding and executing shell commands
2. Reading, writing, and modifying code files
3. Searching codebases and documentation
4. Providing code suggestions and explanations
5. Debugging and troubleshooting

IMPORTANT: When processing user input:
1. For greetings or general questions: 
   Respond naturally and ask how you can help

2. For task requests:
   First say "Let me help you with that. Here's what I'll do:"
   Then list the steps you'll take
   Then ACTUALLY EXECUTE each step using the provided functions
   DO NOT just provide instructions - execute the tasks yourself
   After each step, verify the results and proceed to the next step
   After completing all steps, suggest related improvements

3. For coding tasks:
   First say "I'll help you implement/modify/fix that. Here's my plan:"
   Then list what you'll do
   Then ACTUALLY WRITE/MODIFY the code using write_file()
   DO NOT just suggest code changes - implement them yourself
   After writing code, verify it works
   After completing the implementation, suggest related improvements

4. Always be verbose about what you're doing:
   - "I'm reading file X to understand the current implementation..."
   - "I'm writing the new implementation to file Y..."
   - "I'm executing command Z to test the changes..."
   - "The command completed successfully, moving to next step..."
   - "All steps completed. Here are some suggested improvements..."

5. Format all responses in markdown and include:
   - What you're going to do
   - The actual changes/commands being executed
   - The results/output of each step
   - Verification of results
   - Suggested next steps

6. NEVER just provide instructions or suggestions. Always execute the tasks yourself using:
   - execute_command() for running commands
   - read_file() for reading files
   - write_file() for writing/modifying files

Example interaction:
User: "create a new react app"
You: Let me help you create a React app. Here's what I'll do:

1. Create a new React app using create-react-app
2. Install necessary dependencies
3. Set up initial configuration
4. Start the development server

Starting with step 1:
```shell
$ npx create-react-app my-app
[Output from command]
```

Great! The app is created successfully. Moving to step 2...
[Continue executing remaining steps]

Remember: EXECUTE tasks, don't just suggest them. Be verbose about progress.
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
            cwd = os.getcwd()
            if not check_directory_access(cwd):
                if request_directory_access(cwd):
                    # User granted access, try again
                    return self.execute_command(command)
                return f"Operation cancelled - no access to directory: {cwd}", 1
            
            # Execute command and capture output
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            
            # Log command result
            if result.returncode == 0:
                self.log_progress("Command completed successfully", "green")
            else:
                self.log_progress(f"Command failed with exit code {result.returncode}", "red")
            
            # Return combined output and status
            output = result.stdout + result.stderr
            return output, result.returncode
            
        except Exception as e:
            self.log_progress(f"Error executing command: {str(e)}", "red")
            return str(e), 1
    
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
            
            # Create messages without system prompt
            messages = []
            
            # Add conversation history
            for msg in self.conversation_history[-5:]:  # Keep last 5 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add available functions to the request
            function_context = """
Available functions:
- execute_command(command: str) -> Tuple[str, int]: Execute a shell command and return its actual output
- read_file(path: str) -> str: Read contents of a file
- write_file(path: str, content: str) -> str: Write content to a file

Current working directory: {cwd}
Sudo access: {sudo}

IMPORTANT: When executing commands:
1. First explain what you're going to do
2. Then EXECUTE the tasks - don't just suggest them
3. Show the actual command output
4. Verify the results
5. Continue with next steps
6. Be verbose about progress
7. Format all output in markdown

Example of good response:
"Let me help you with that. I'll create a new directory and initialize a git repo:

Creating the directory:
```shell
$ mkdir my-project
[Directory created successfully]
```

Initializing git repo:
```shell
$ cd my-project && git init
[Git repository initialized successfully]
```

Great! The repository is ready. Now I'll..."
""".format(
    cwd=os.getcwd(),
    sudo="available" if check_sudo_access() else "not configured"
)
            
            # Add user's request with function context
            messages.append({
                "role": "user",
                "content": function_context + "\n" + request
            })
            
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
            
            # Check if the response contains a command to execute
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
                    output, status = self.execute_command(command)
                    # Replace the command in the response with actual output
                    placeholder = f'execute_command("{command}")'
                    replacement = f"```shell\n$ {command}\n{output}\n```"
                    if status != 0:
                        replacement += f"\nCommand failed with exit code {status}"
                    response_text = response_text.replace(placeholder, replacement)
            else:
                # If no command was executed but one was needed, execute it
                if any(keyword in request.lower() for keyword in ["list", "show", "display", "find", "search"]):
                    # Determine the appropriate command based on the request
                    command = None
                    if "tree" in request.lower():
                        command = "tree"
                    elif "list" in request.lower() or "show" in request.lower():
                        command = "ls -la"
                    
                    if command:
                        output, status = self.execute_command(command)
                        response_text = f"""Let me show you the contents:

```shell
$ {command}
{output}
```"""
                        if status != 0:
                            response_text += f"\nCommand failed with exit code {status}"
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": request  # Store original request without function context
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Log completion
            self.log_progress("Request processed successfully", "green")
            
            return response_text
            
        except Exception as e:
            self.log_progress(f"Error processing request: {str(e)}", "red")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.log_progress("Conversation history cleared")
    
    def compact_history(self):
        """Compact history by summarizing old messages."""
        if len(self.conversation_history) <= 6:  # Keep if small
            return
            
        # Summarize old messages
        self.log_progress("Compacting conversation history...")
        old_messages = self.conversation_history[:-6]  # All except last 6
        
        try:
            summary = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": msg["role"],
                    "content": msg["content"]
                } for msg in old_messages],
                system="Please summarize the previous conversation very concisely.",
                temperature=0.7
            )
            
            # Keep summary and last 6 messages
            self.conversation_history = [
                {"role": "assistant", "content": f"Previous conversation summary: {summary.content[0].text}"},
                *self.conversation_history[-6:]
            ]
            self.log_progress("History compacted successfully", "green")
        except Exception as e:
            self.log_progress(f"Error summarizing history: {str(e)}", "red") 