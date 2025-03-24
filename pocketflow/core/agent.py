import logging
from typing import Optional
from .node import Node
from .state import SharedState, TaskStatus

logger = logging.getLogger('ShellAgent')

class ShellAgent:
    """A shell coding agent that safely executes commands"""
    def __init__(self):
        logger.info("Initializing ShellAgent")
        self.shared_state = SharedState()
        
        # Initialize nodes
        from ..nodes.request import RequestHandlerNode
        from ..nodes.classifier import TaskClassifierNode
        from ..nodes.selector import ToolSelectorNode
        from ..nodes.context import ContextManagerNode
        from ..nodes.response import ResponseGeneratorNode
        
        self.request_handler = RequestHandlerNode()
        self.task_classifier = TaskClassifierNode()
        self.tool_selector = ToolSelectorNode()
        self.context_manager = ContextManagerNode()
        self.response_generator = ResponseGeneratorNode()

        # Initialize utilities
        from ..utils.command import CommandParser
        from ..utils.state import StateManager
        from ..utils.formatter import ResponseFormatter
        from ..utils.analyzer import CodeAnalyzer
        from ..utils.file import FileOperator
        from ..utils.interpreter import AIInterpreter
        
        self.command_parser = CommandParser()
        self.state_manager = StateManager()
        self.response_formatter = ResponseFormatter()
        self.code_analyzer = CodeAnalyzer()
        self.file_operator = FileOperator()
        self.ai_interpreter = AIInterpreter()

    def process_request(self, request: str) -> str:
        """Process a user request and return the response."""
        logger.info(f"Processing new request: {request}")
        
        # Initialize request
        self.shared_state.request["raw"] = request
        self.shared_state.task["status"] = TaskStatus.RUNNING.value

        try:
            # Execute flow
            current_node = self.request_handler
            while current_node:
                # Prep
                prep_data = current_node.prep(self.shared_state)
                
                # Exec
                exec_result = current_node.exec(prep_data)
                
                # Post
                next_action = current_node.post(self.shared_state, prep_data, exec_result)
                
                # Route to next node
                if next_action == "error":
                    logger.error(f"Error in {current_node.name}")
                    break
                elif next_action == "complete":
                    logger.info("Flow completed successfully")
                    break
                
                # Select next node based on action
                current_node = self._get_next_node(current_node, next_action)

            # Update final status
            self.shared_state.task["status"] = (
                TaskStatus.ERROR.value if self.shared_state.result["error"]
                else TaskStatus.COMPLETE.value
            )

            return self.shared_state.result.get("formatted_response", "No response generated")

        except Exception as e:
            logger.exception("Error processing request")
            self.shared_state.result["error"] = str(e)
            self.shared_state.task["status"] = TaskStatus.ERROR.value
            return f"Error: {str(e)}"

    def _get_next_node(self, current_node: Node, action: str) -> Optional[Node]:
        """Get the next node based on the current node and action."""
        node_map = {
            "RequestHandler": {
                "classify": self.task_classifier,
                "error": None
            },
            "TaskClassifier": {
                "shell": self.tool_selector,
                "coding": self.tool_selector,
                "integrated": self.tool_selector,
                "error": None
            },
            "ToolSelector": {
                "execute": self.context_manager,
                "error": None
            },
            "ContextManager": {
                "default": self.response_generator,
                "error": None
            },
            "ResponseGenerator": {
                "complete": None,
                "error": None
            }
        }
        
        next_node = node_map.get(current_node.name, {}).get(action)
        logger.debug(f"Routing from {current_node.name} to {next_node.name if next_node else 'None'}")
        return next_node 