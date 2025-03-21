from typing import Dict, Any
from ..core.node import Node
from ..core.state import SharedState, TaskType

class TaskClassifierNode(Node):
    """Node for classifying tasks"""
    def __init__(self):
        super().__init__("TaskClassifier")

    def prep(self, shared: SharedState) -> Dict[str, Any]:
        logger.info(f"Classifying task for command: {shared.request['interpreted']['command']}")
        return shared.request["interpreted"]

    def exec(self, data: Dict[str, Any]) -> TaskType:
        command = data["command"]
        parameters = data["parameters"]
        
        # Simple classification logic - can be enhanced
        if any(keyword in command.lower() for keyword in ["code", "file", "script"]):
            if any(keyword in command.lower() for keyword in ["run", "execute", "shell"]):
                return TaskType.INTEGRATED
            return TaskType.CODING
        return TaskType.SHELL

    def post(self, shared: SharedState, data: Dict[str, Any], result: TaskType) -> str:
        shared.task["type"] = result.value
        logger.info(f"Classified task as: {result.value}")
        return result.value 