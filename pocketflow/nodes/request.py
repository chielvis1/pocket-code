from datetime import datetime
from typing import Dict, Any
from ..core.node import Node
from ..core.state import SharedState
from ..utils.interpreter import AIInterpreter

class RequestHandlerNode(Node):
    """Node for handling user requests"""
    def __init__(self):
        super().__init__("RequestHandler")
        self.ai_interpreter = AIInterpreter()

    def prep(self, shared: SharedState) -> Dict[str, Any]:
        logger.info(f"Processing request: {shared.request['raw']}")
        return {
            "raw": shared.request["raw"],
            "timestamp": datetime.now().isoformat()
        }

    def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize and interpret request
        normalized = self.ai_interpreter.normalize_request(data["raw"])
        command, parameters = self.ai_interpreter.extract_command(normalized)
        confidence = self.ai_interpreter.calculate_confidence(command, parameters)
        
        logger.info(f"Interpreted command: {command} with confidence: {confidence}")
        return {
            "command": command,
            "parameters": parameters,
            "confidence": confidence
        }

    def post(self, shared: SharedState, data: Dict[str, Any], result: Dict[str, Any]) -> str:
        shared.request["interpreted"] = result
        if result["confidence"] < 0.7:
            logger.warning(f"Low confidence in request interpretation: {result['confidence']}")
            shared.result["error"] = "Low confidence in request interpretation"
            return "error"
        return "classify" 