from typing import Dict, Any
from ..core.node import Node
from ..core.state import SharedState, TaskType
from ..utils.command import CommandParser
from ..utils.state import StateManager
from ..utils.analyzer import CodeAnalyzer
from ..utils.file import FileOperator

class ToolSelectorNode(Node):
    """Node for selecting appropriate tools"""
    def __init__(self):
        super().__init__("ToolSelector")
        self.command_parser = CommandParser()
        self.state_manager = StateManager()
        self.code_analyzer = CodeAnalyzer()
        self.file_operator = FileOperator()

    def prep(self, shared: SharedState) -> Dict[str, Any]:
        logger.info(f"Selecting tools for task type: {shared.task['type']}")
        return {
            "type": shared.task["type"],
            "request": shared.request["interpreted"]
        }

    def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = data["type"]
        tools = []
        configs = {}

        # Select tools based on task type
        if task_type in [TaskType.SHELL.value, TaskType.INTEGRATED.value]:
            tools.extend(["command_parser", "state_manager"])
        if task_type in [TaskType.CODING.value, TaskType.INTEGRATED.value]:
            tools.extend(["code_analyzer", "file_operator"])

        logger.info(f"Selected tools: {tools}")
        return {"tools": tools, "configs": configs}

    def post(self, shared: SharedState, data: Dict[str, Any], result: Dict[str, Any]) -> str:
        shared.task["tools"] = result["tools"]
        shared.context["tool_configs"] = result["configs"]
        logger.info(f"Configured tools: {result['tools']}")
        return "execute" 