from typing import Dict, Any
from ..core.node import Node
from ..core.state import SharedState
from ..utils.state import StateManager

class ContextManagerNode(Node):
    """Node for managing context across operations"""
    def __init__(self):
        super().__init__("ContextManager")
        self.state_manager = StateManager()

    def prep(self, shared: SharedState) -> Dict[str, Any]:
        logger.info("Preparing context update")
        return {
            "state": shared.context,
            "task": shared.task,
            "request": shared.request
        }

    def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Update context based on current state
        working_dir = self.state_manager.get_working_dir()
        env_vars = self.state_manager.get_env_vars()
        history = self.state_manager.get_command_history()

        logger.info(f"Updated working directory: {working_dir}")
        return {
            "working_dir": working_dir,
            "env_vars": env_vars,
            "command_history": history
        }

    def post(self, shared: SharedState, data: Dict[str, Any], result: Dict[str, Any]) -> str:
        shared.context.update(result)
        if not self.validate_context(shared.context):
            logger.error("Context validation failed")
            shared.result["error"] = "Context validation failed"
            return "error"
        return "default"

    def validate_context(self, context: Dict[str, Any]) -> bool:
        return all(key in context for key in ["working_dir", "env_vars", "command_history"]) 