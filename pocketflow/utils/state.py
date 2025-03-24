from datetime import datetime
from typing import Dict, Any, List
import os
import logging
from ..core.state import CommandHistory

logger = logging.getLogger('ShellAgent')

class StateManager:
    """Utility for managing shell state"""
    def __init__(self):
        self.state = {
            "working_dir": os.getcwd(),
            "env_vars": dict(os.environ),
            "command_history": [],
            "last_output": None
        }

    def update_state(self, command: str, output: str) -> None:
        """Update state after command execution"""
        self.state["command_history"].append({
            "command": command,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })
        self.state["last_output"] = output

    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return self.state.copy()

    def get_working_dir(self) -> str:
        return self.state["working_dir"]

    def get_env_vars(self) -> Dict[str, str]:
        return self.state["env_vars"]

    def get_command_history(self) -> List[CommandHistory]:
        return self.state["command_history"] 