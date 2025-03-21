import re
from typing import Dict, Any
import logging

logger = logging.getLogger('ShellAgent')

class CommandParser:
    """Utility for parsing and validating shell commands"""
    def parse_command(self, command: str) -> Dict[str, Any]:
        logger.debug(f"Parsing command: {command}")
        parts = command.split()
        return {
            "command": parts[0] if parts else "",
            "args": parts[1:] if len(parts) > 1 else [],
            "raw": command
        }

    def is_safe_command(self, command: str) -> bool:
        logger.debug(f"Checking command safety: {command}")
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"mkfs",
            r"dd\s+if=",
            r">\s+/dev/",
            r"chmod\s+777",
            r"sudo",
            r"su\s+",
            r"passwd"
        ]
        return not any(re.search(pattern, command, re.IGNORECASE) for pattern in dangerous_patterns) 