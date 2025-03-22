"""AI Agent implementation using Anthropic's Claude."""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

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
1. For greetings or general questions: Respond naturally and ask how you can help
2. For task requests: Execute them directly using the provided functions - DO NOT just provide instructions
3. For coding tasks: Execute the necessary commands to complete the task - DO NOT just suggest commands
4. Format all responses in markdown
5. Be concise unless details are requested
6. NEVER simulate or make up command outputs - always use the actual output from execute_command()
7. When executing commands, ALWAYS use the execute_command() function
8. For complex tasks, break them down into steps and execute each step
9. After executing commands, verify the results and proceed with next steps

Example interactions:
User: "hello"
You: "Hello! How can I help you with your coding tasks today?"

User: "create a new react app"
You: I'll create a new React app for you:
```shell
output = execute_command("npx create-react-app my-app")
```
React app created successfully! Let's start it:
```shell
output = execute_command("cd my-app && npm start")
```

Please format your responses in markdown and be concise unless asked for details.
"""
    
    def execute_command(self, command: str) -> Tuple[str, int]:
        """Execute a shell command and return output and status."""
        try:
            # Check if command needs sudo
            needs_sudo = command.startswith("sudo ")
            if needs_sudo and not check_sudo_access():
                if request_sudo_access():
                    console.print("[yellow]Please run the command again after configuring sudo access[/yellow]")
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
            
            # Return combined output and status
            output = result.stdout + result.stderr
            return output, result.returncode
            
        except Exception as e:
            return str(e), 1
    
    def read_file(self, path: str) -> str:
        """Read contents of a file."""
        try:
            # Check directory access
            dir_path = str(Path(path).parent)
            if not check_directory_access(dir_path):
                if request_directory_access(dir_path):
                    # User granted access, try again
                    return self.read_file(path)
                return f"Operation cancelled - no access to directory: {dir_path}"
            
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        try:
            # Check directory access
            dir_path = str(Path(path).parent)
            if not check_directory_access(dir_path):
                if request_directory_access(dir_path):
                    # User granted access, try again
                    return self.write_file(path, content)
                return f"Operation cancelled - no access to directory: {dir_path}"
            
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def process_request(self, request: str) -> str:
        """Process a user request through Claude."""
        try:
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
1. Use execute_command() to run the command and get its actual output
2. NEVER simulate or make up command outputs
3. Always show the actual command being run
4. Format command output in a code block with the command at the top
5. ALWAYS execute commands - do not just suggest them
6. For complex tasks, execute each step and verify the results
7. If a command fails, try to fix the issue or ask for help
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
                        response_text = f"```shell\n$ {command}\n{output}\n```"
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
            
            return response_text
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def compact_history(self):
        """Compact history by summarizing old messages."""
        if len(self.conversation_history) <= 6:  # Keep if small
            return
            
        # Summarize old messages
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
        except Exception as e:
            console.print(f"[red]Error summarizing history:[/red] {str(e)}") 