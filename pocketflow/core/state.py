from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
import os

class TaskType(Enum):
    SHELL = "shell"
    CODING = "coding"
    INTEGRATED = "integrated"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class CommandHistory:
    command: str
    output: str
    timestamp: str

@dataclass
class SharedState:
    # Request Data
    request: Dict[str, Any] = None
    # Task Data
    task: Dict[str, Any] = None
    # Context Data
    context: Dict[str, Any] = None
    # Result Data
    result: Dict[str, Any] = None

    def __post_init__(self):
        self.request = {
            "raw": "",
            "timestamp": datetime.now().isoformat(),
            "interpreted": {
                "command": "",
                "confidence": 0.0,
                "parameters": {}
            }
        }
        self.task = {
            "type": None,
            "tools": [],
            "status": TaskStatus.PENDING.value
        }
        self.context = {
            "working_dir": os.getcwd(),
            "env_vars": dict(os.environ),
            "command_history": [],
            "last_output": None
        }
        self.result = {
            "output": None,
            "error": None,
            "metadata": {}
        } 