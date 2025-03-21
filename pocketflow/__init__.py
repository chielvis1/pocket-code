"""PocketFlow - A framework for building AI-powered shell and coding agents"""

from .core.agent import ShellAgent
from .core.node import Node
from .core.state import TaskType, TaskStatus, CommandHistory, SharedState

__version__ = "0.1.0"
__all__ = [
    "ShellAgent",
    "Node",
    "TaskType",
    "TaskStatus",
    "CommandHistory",
    "SharedState"
]