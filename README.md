# AI Shell and Coding Agent

An intelligent agent that seamlessly handles both coding and shell operations through natural language commands, built using the [PocketFlow](https://github.com/The-Pocket/PocketFlow) framework.

## Overview

This agent is designed to be your AI pair programming assistant, capable of:
- Understanding and executing natural language coding requests
- Managing shell operations with proper validation
- Maintaining context across multiple operations
- Performing complex code analysis and modifications
- **NEW**: Directly controlling the host terminal with interactive process support
- **NEW**: Maintaining long-term context across sessions
- **NEW**: Preventing hallucinations with task tracking and response grounding

## Features

### Coding Capabilities
- **Code Search**: Search codebases using semantic understanding or patterns
- **Code Analysis**: Understand code structure and dependencies
- **Code Editing**: Make changes while preserving style and context
- **Testing Support**: Help with test creation and verification

### Shell Capabilities
- **Command Execution**: Run shell commands with state management
- **File Operations**: Handle file system tasks safely
- **Script Generation**: Create and execute automation scripts
- **Environment Management**: Track and modify system state
- **NEW**: Interactive Process Support: Start, interact with, and terminate long-running processes
- **NEW**: Direct Terminal Control: Control the actual host terminal instead of virtual environments

### AI Features
- **Natural Language Understanding**: Convert requests to actions
- **Context Awareness**: Remember previous operations
- **Safety Checks**: Validate all operations before execution
- **Smart Suggestions**: Provide intelligent recommendations
- **NEW**: Persistent Context: Maintain full conversation history across sessions
- **NEW**: Task Management: Create and track explicit task lists for each request
- **NEW**: Response Grounding: Verify file/directory references and detect hypothetical language

## Architecture

### Flow Design
```mermaid
graph TD
    %% Main Flow Nodes
    A[Request Handler] -->|classify| B[Task Classifier]
    B -->|shell| C[Tool Selector]
    B -->|coding| C
    B -->|integrated| C
    C -->|execute| D[Context Manager]
    D -->|default| E[Response Generator]
    E -->|complete| F[End]

    %% Utility Functions
    subgraph "Utility Functions"
        G[Command Parser]
        H[State Manager]
        I[Response Formatter]
        J[Code Analyzer]
        K[File Operator]
        L[AI Interpreter]
        M[Task Manager]
        N[Response Grounder]
        O[Terminal Controller]
    end

    %% Node to Utility Connections
    A -->|uses| L
    C -->|uses| G
    C -->|uses| H
    C -->|uses| J
    C -->|uses| K
    C -->|uses| O
    D -->|uses| H
    E -->|uses| I
    E -->|uses| M
    E -->|uses| N
```

### Core Components

#### 1. Node System
Each operation is handled by specialized nodes:

- **RequestHandlerNode**: Processes natural language requests
- **TaskClassifierNode**: Determines if task is coding, shell, or both
- **ToolSelectorNode**: Picks appropriate tools for the task
- **ContextManagerNode**: Maintains operation history and state
- **ResponseGeneratorNode**: Formats and returns results

#### 2. State Management
```python
@dataclass
class SharedState:
    request: Dict[str, Any]  # Current request info
    task: Dict[str, Any]     # Task classification
    context: Dict[str, Any]  # Environment state
    result: Dict[str, Any]   # Operation results
```

#### 3. Utility Functions
- **CommandParser**: Shell command validation
- **StateManager**: Environment state tracking
- **ResponseFormatter**: Output standardization
- **CodeAnalyzer**: Code understanding
- **FileOperator**: File system operations
- **AIInterpreter**: Natural language processing
- **NEW - TaskManager**: Creates and tracks explicit task lists
- **NEW - ResponseGrounder**: Verifies references and detects hypothetical language
- **NEW - TerminalController**: Directly controls the host terminal

## Usage Examples

### 1. Code Operations
```python
# Find specific code patterns
agent.process_request("find all API endpoint definitions")

# Make code changes
agent.process_request("add error handling to the file upload function")

# Code analysis
agent.process_request("explain the authentication flow in this codebase")
```

### 2. Shell Operations
```python
# File operations
agent.process_request("organize all JavaScript files into a src directory")

# System monitoring
agent.process_request("show me current memory usage")

# Environment setup
agent.process_request("set up a Python virtual environment and install requirements")

# NEW - Interactive processes
agent.process_request("start a Python REPL and help me debug this function")

# NEW - Long-running operations
agent.process_request("monitor the log file and alert me when errors occur")
```

### 3. Integrated Tasks
```python
# Combined operations
agent.process_request("find TODOs in the codebase and create issues for each")

# Development workflow
agent.process_request("run tests, format code, and commit changes")

# Project setup
agent.process_request("initialize a new React project and set up ESLint")

# NEW - Complex multi-step tasks
agent.process_request("analyze this codebase, identify performance bottlenecks, and implement optimizations")
```

## Getting Started

### Installation
```bash
# Clone the repository
git clone https://github.com/chielvis1/pocket-code.git

# Install dependencies
pip install -r requirements.txt
pip install pexpect  # NEW dependency for terminal control

# Install the CLI tool
pip install -e .
```

### Usage

1. Open your terminal and start the interactive interface:
```bash
pcode
```

2. First-time setup:
```bash
# Configure your API key
/login    # This will open your browser for API key configuration

# View available commands
/help     # Shows all available commands and their descriptions
```

3. Common Commands:
```bash
/clear          # Clear conversation history and free up context
/compact        # Clear conversation history but keep a summary
/config         # Open configuration panel
/cost           # Show total cost and duration of current session
/doctor         # Check health of your installation
/exit (quit)    # Exit the REPL
/help           # Show help and available commands
/init           # Initialize a new documentation file
```

4. Example Interactions:
```bash
> analyze the current directory structure
Analyzing... Found 5 Python files, 2 JavaScript files...

> create a new API endpoint for user authentication
Creating endpoint... Generated code in auth/views.py...

> run tests for the user module
Running pytest for user module...

> start a Python REPL and help me debug this function
Starting Python REPL...
>>> def calculate_total(items):
...     return sum(item.price for item in items)
...
```

### Basic Usage
```python
from agent import ShellAgent

# Initialize the agent
agent = ShellAgent()

# Process a request
response = agent.process_request("help me understand this codebase")

# Access results
print(response.explanation)
print(response.changes)
```

### Advanced Configuration
```python
from agent import ShellAgent, TaskType, SharedState

# Configure with custom settings
agent = ShellAgent(
    working_dir="/path/to/project",
    safety_checks=True,
    verbose_logging=True,
    persistent_context=True,  # NEW: Enable persistent context
    task_tracking=True        # NEW: Enable task tracking
)
```

## Development

### Adding New Capabilities
```python
from agent.core import Node

class CustomAnalyzer(Node):
    def prep(self, shared):
        # Prepare analysis
        return data

    def exec(self, data):
        # Perform analysis
        return result

    def post(self, shared, data, result):
        # Update state
        return "next_node"
```

## Recent Improvements

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for detailed information about recent enhancements to:

1. **Context Management**: Persistent storage and full history retention
2. **Host Terminal Control**: Direct terminal interaction with interactive process support
3. **Hallucination Prevention**: Task tracking and response grounding

## Contributing

Contributions are welcome! Please check our [Contributing Guide](CONTRIBUTING.md).

## Credits

### Authors
- **Elvis Chi** - *Creator and Lead Developer*
  - Designed and implemented the AI coding agent architecture
  - Created the interactive CLI interface
  - Integrated with PocketFlow framework

### Built With
- [PocketFlow](https://github.com/The-Pocket/PocketFlow) - The powerful framework that made this agent possible
- Python 3.8+
- Modern AI/ML libraries

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
