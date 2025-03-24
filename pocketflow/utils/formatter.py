from typing import Dict, Any, Optional
import logging
from ..core.state import TaskType

logger = logging.getLogger('ShellAgent')

class ResponseFormatter:
    """Utility for formatting command responses"""
    def format_by_task_type(self, data: Dict[str, Any]) -> str:
        task_type = data["task"]["type"]
        if task_type == TaskType.SHELL.value:
            return self.format_success(data["result"]["output"])
        elif task_type == TaskType.CODING.value:
            return self.format_success(data["result"]["analysis"])
        else:
            return self.format_success(str(data["result"]))

    def add_context_info(self, response: str, context: Dict[str, Any]) -> str:
        return f"{response}\n\n{self.format_state(context)}"

    def add_error_info(self, response: str, error: Optional[str]) -> str:
        if error:
            return f"{response}\n\n{self.format_error(error)}"
        return response

    def format_success(self, output: str) -> str:
        """Format successful command output"""
        return f"Command executed successfully:\n```\n{output}\n```"

    def format_error(self, error: str) -> str:
        """Format error message"""
        return f"Error: {error}"

    def format_state(self, state: Dict[str, Any]) -> str:
        """Format current state information"""
        return f"""
Current State:
- Working Directory: {state['working_dir']}
- Last Command Output: {state['last_output']}
- Command History: {len(state['command_history'])} commands
"""

    def log_response(self, response: str) -> None:
        logger.debug(f"Logging response: {response}") 