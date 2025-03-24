"""Node for managing context across operations."""

import logging
from typing import Dict, Any
from ..core.node import Node
from ..core.state import SharedState
from ..utils.state import StateManager
from ..utils.context_manager import EnhancedContextManager

logger = logging.getLogger('ShellAgent')

class ContextManagerNode(Node):
    """Node for managing context across operations"""
    def __init__(self):
        super().__init__("ContextManager")
        self.state_manager = StateManager()
        self.enhanced_context = EnhancedContextManager()

    def prep(self, shared: SharedState) -> Dict[str, Any]:
        """Prepare context update."""
        logger.info("Preparing context update")
        return {
            "state": shared.context,
            "task": shared.task,
            "request": shared.request
        }

    def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute context management operations."""
        # Update context based on current state
        working_dir = self.state_manager.get_working_dir()
        env_vars = self.state_manager.get_env_vars()
        history = self.state_manager.get_command_history()

        # Update enhanced context
        self.enhanced_context.update_state(
            working_dir=working_dir,
            env_vars=env_vars,
            command_history=history
        )

        # Add the current request to conversation history
        if data["request"].get("raw"):
            self.enhanced_context.add_message("user", data["request"]["raw"])

        # Get full context for AI model
        full_context = self.enhanced_context.get_full_context()

        logger.info(f"Updated working directory: {working_dir}")
        logger.info(f"Context updated with {len(full_context['conversation_history'])} messages in history")
        
        return {
            "working_dir": working_dir,
            "env_vars": env_vars,
            "command_history": history,
            "conversation_history": full_context["conversation_history"],
            "context_summary": full_context.get("summary", "")
        }

    def post(self, shared: SharedState, data: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Post-process context management results."""
        # Update shared state with context information
        shared.context.update(result)
        
        # Store conversation history in shared state for other nodes
        if "conversation_history" not in shared.context:
            shared.context["conversation_history"] = []
        shared.context["conversation_history"] = result.get("conversation_history", [])
        
        # Store context summary
        shared.context["context_summary"] = result.get("context_summary", "")
        
        if not self.validate_context(shared.context):
            logger.error("Context validation failed")
            shared.result["error"] = "Context validation failed"
            return "error"
        return "default"

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate context data."""
        # Check for required context fields
        required_fields = ["working_dir", "env_vars", "command_history"]
        for field in required_fields:
            if field not in context:
                logger.error(f"Missing required context field: {field}")
                return False
                
        # Validate working directory exists
        if not context["working_dir"]:
            logger.error("Working directory is empty")
            return False
            
        return True
        
    def add_response_to_history(self, response: str):
        """Add AI response to conversation history."""
        self.enhanced_context.add_message("assistant", response)
        
    def summarize_context(self, model_function):
        """Generate a summary of the current conversation."""
        return self.enhanced_context.generate_summary(model_function)
