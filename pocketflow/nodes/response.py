from typing import Dict, Any, Optional
from ..core.node import Node
from ..core.state import SharedState, TaskType
from ..utils.formatter import ResponseFormatter

class ResponseGeneratorNode(Node):
    """Node for generating formatted responses"""
    def __init__(self):
        super().__init__("ResponseGenerator")
        self.response_formatter = ResponseFormatter()

    def prep(self, shared: SharedState) -> Dict[str, Any]:
        logger.info("Preparing response")
        return {
            "request": shared.request,
            "task": shared.task,
            "context": shared.context,
            "result": shared.result
        }

    def exec(self, data: Dict[str, Any]) -> str:
        # Format response based on task type and result
        formatted = self.response_formatter.format_by_task_type(data)
        with_context = self.response_formatter.add_context_info(formatted, data["context"])
        final_response = self.response_formatter.add_error_info(with_context, data["result"]["error"])

        logger.info("Generated formatted response")
        return final_response

    def post(self, shared: SharedState, data: Dict[str, Any], result: str) -> str:
        shared.result["formatted_response"] = result
        self.response_formatter.log_response(result)
        logger.info("Response generation complete")
        return "complete" 