import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shell_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ShellAgent')

class Node:
    """Base class for all nodes in the flow"""
    def __init__(self, name: str):
        self.name = name
        logger.info(f"Initialized {self.__class__.__name__}")

    def prep(self, shared: Any) -> Any:
        logger.debug(f"{self.name}: Starting prep")
        return None

    def exec(self, data: Any) -> Any:
        logger.debug(f"{self.name}: Starting exec")
        return None

    def post(self, shared: Any, data: Any, result: Any) -> str:
        logger.debug(f"{self.name}: Starting post")
        return "default" 