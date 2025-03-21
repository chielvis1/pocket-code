from typing import Dict, Any, Optional
import logging
import re

logger = logging.getLogger('ShellAgent')

class AIInterpreter:
    """Utility for interpreting natural language into commands"""
    def interpret(self, text: str) -> Dict[str, Any]:
        """Interpret natural language into command structure"""
        # Normalize text
        text = text.lower().strip()
        
        # Extract command and parameters
        command = self.extract_command(text)
        params = self.extract_parameters(text)
        
        # Calculate confidence
        confidence = self.calculate_confidence(text, command)
        
        return {
            "command": command,
            "parameters": params,
            "confidence": confidence
        }

    def extract_command(self, text: str) -> str:
        """Extract command from text"""
        # Common command patterns
        patterns = {
            r'list\s+files?': 'ls',
            r'create\s+directory': 'mkdir',
            r'delete\s+file': 'rm',
            r'move\s+file': 'mv',
            r'copy\s+file': 'cp',
            r'read\s+file': 'cat',
            r'write\s+to\s+file': 'echo',
            r'change\s+directory': 'cd',
            r'print\s+working\s+directory': 'pwd',
            r'search\s+in\s+files?': 'grep'
        }
        
        for pattern, cmd in patterns.items():
            if re.search(pattern, text):
                return cmd
        return ""

    def extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract command parameters"""
        params = {}
        
        # Extract file paths
        file_paths = re.findall(r'["\']?([^"\'\s]+\.\w+)["\']?', text)
        if file_paths:
            params["files"] = file_paths
            
        # Extract directory paths
        dir_paths = re.findall(r'["\']?([^"\'\s]+/+)["\']?', text)
        if dir_paths:
            params["directories"] = dir_paths
            
        # Extract search terms
        search_terms = re.findall(r'search\s+for\s+["\']?([^"\']+)["\']?', text)
        if search_terms:
            params["search_term"] = search_terms[0]
            
        return params

    def calculate_confidence(self, text: str, command: str) -> float:
        """Calculate interpretation confidence"""
        if not command:
            return 0.0
            
        # Base confidence on command match
        confidence = 0.5
        
        # Increase confidence if parameters are present
        if re.search(r'["\']?([^"\'\s]+\.\w+)["\']?', text):  # File paths
            confidence += 0.2
        if re.search(r'["\']?([^"\'\s]+/+)["\']?', text):  # Directory paths
            confidence += 0.2
        if re.search(r'search\s+for\s+["\']?([^"\']+)["\']?', text):  # Search terms
            confidence += 0.1
            
        return min(confidence, 1.0)

    def log_interpretation(self, interpretation: Dict[str, Any]) -> None:
        logger.debug(f"Logging interpretation: {interpretation}") 