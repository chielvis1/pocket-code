"""Grounding utilities to prevent hallucinations in AI responses."""

import logging
import re
import os
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger('ShellAgent')

class ResponseGrounder:
    """Utility for grounding AI responses in reality to prevent hallucinations."""
    
    def __init__(self):
        """Initialize the response grounder."""
        self.verification_patterns = {
            "file_existence": r'(?:file|open|read|write|modify)\s+[\'"]?([^\s\'"]+\.\w+)[\'"]?',
            "directory_existence": r'(?:directory|folder|cd|mkdir)\s+[\'"]?([^\s\'"]+/?)[\'"]?',
            "command_execution": r'(?:run|execute|launch)\s+[\'"]?([^\s\'"]+)[\'"]?',
            "hypothetical_markers": [
                r'(?:imagine|let\'s say|suppose|for example|hypothetically|pretend)',
                r'(?:we could|you could|one could|we can|you can)',
                r'(?:would look like|might look like|could look like)',
                r'(?:would be|might be|could be|would have|might have|could have)'
            ]
        }
        logger.info("ResponseGrounder initialized")
    
    def verify_file_references(self, text: str) -> List[Dict[str, Any]]:
        """Verify that files referenced in text actually exist.
        
        Args:
            text: Text to check for file references
            
        Returns:
            List of verification results
        """
        results = []
        pattern = self.verification_patterns["file_existence"]
        
        # Find all file references
        matches = re.finditer(pattern, text)
        for match in matches:
            file_path = match.group(1)
            
            # Skip if it's a common command or not a file path
            if file_path in ['file', 'open', 'read', 'write', 'cat', 'touch', 'rm']:
                continue
                
            # Normalize path
            if not file_path.startswith('/'):
                file_path = os.path.join(os.getcwd(), file_path)
            
            # Check if file exists
            exists = os.path.isfile(file_path)
            
            results.append({
                "type": "file",
                "path": file_path,
                "exists": exists,
                "match": match.group(0)
            })
        
        return results
    
    def verify_directory_references(self, text: str) -> List[Dict[str, Any]]:
        """Verify that directories referenced in text actually exist.
        
        Args:
            text: Text to check for directory references
            
        Returns:
            List of verification results
        """
        results = []
        pattern = self.verification_patterns["directory_existence"]
        
        # Find all directory references
        matches = re.finditer(pattern, text)
        for match in matches:
            dir_path = match.group(1)
            
            # Skip if it's a common command or not a directory path
            if dir_path in ['directory', 'folder', 'cd', 'mkdir', 'rmdir', 'ls']:
                continue
                
            # Normalize path
            if not dir_path.startswith('/'):
                dir_path = os.path.join(os.getcwd(), dir_path)
            
            # Check if directory exists
            exists = os.path.isdir(dir_path)
            
            results.append({
                "type": "directory",
                "path": dir_path,
                "exists": exists,
                "match": match.group(0)
            })
        
        return results
    
    def detect_hypotheticals(self, text: str) -> List[Dict[str, Any]]:
        """Detect hypothetical language that might indicate hallucinations.
        
        Args:
            text: Text to check for hypothetical language
            
        Returns:
            List of detected hypothetical markers
        """
        results = []
        
        for pattern in self.verification_patterns["hypothetical_markers"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get some context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                results.append({
                    "type": "hypothetical",
                    "marker": match.group(0),
                    "context": context
                })
        
        return results
    
    def verify_command_references(self, text: str, valid_commands: List[str]) -> List[Dict[str, Any]]:
        """Verify that commands referenced in text are valid.
        
        Args:
            text: Text to check for command references
            valid_commands: List of valid commands to check against
            
        Returns:
            List of verification results
        """
        results = []
        pattern = self.verification_patterns["command_execution"]
        
        # Find all command references
        matches = re.finditer(pattern, text)
        for match in matches:
            command = match.group(1)
            
            # Skip if it's a common verb or not a command
            if command in ['run', 'execute', 'launch']:
                continue
                
            # Check if command is valid
            is_valid = command in valid_commands
            
            results.append({
                "type": "command",
                "command": command,
                "valid": is_valid,
                "match": match.group(0)
            })
        
        return results
    
    def ground_response(self, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Ground a response by checking for hallucinations and adding warnings.
        
        Args:
            response: Response to ground
            
        Returns:
            Tuple of (grounded_response, verification_results)
        """
        # Collect all verification results
        verification_results = []
        
        # Verify file references
        file_results = self.verify_file_references(response)
        verification_results.extend(file_results)
        
        # Verify directory references
        dir_results = self.verify_directory_references(response)
        verification_results.extend(dir_results)
        
        # Detect hypothetical language
        hypothetical_results = self.detect_hypotheticals(response)
        verification_results.extend(hypothetical_results)
        
        # If we found any issues, add warnings to the response
        grounded_response = response
        if verification_results:
            warning_text = "\n\n**VERIFICATION WARNINGS:**\n\n"
            
            # Add file existence warnings
            nonexistent_files = [r for r in file_results if not r["exists"]]
            if nonexistent_files:
                warning_text += "- **File references that don't exist:**\n"
                for result in nonexistent_files:
                    warning_text += f"  - {result['path']}\n"
            
            # Add directory existence warnings
            nonexistent_dirs = [r for r in dir_results if not r["exists"]]
            if nonexistent_dirs:
                warning_text += "- **Directory references that don't exist:**\n"
                for result in nonexistent_dirs:
                    warning_text += f"  - {result['path']}\n"
            
            # Add hypothetical language warnings
            if hypothetical_results:
                warning_text += "- **Hypothetical language detected:**\n"
                for result in hypothetical_results[:3]:  # Limit to first 3
                    warning_text += f"  - \"{result['marker']}\" in context: \"...{result['context']}...\"\n"
            
            # Add the warnings to the response
            grounded_response += warning_text
        
        return grounded_response, verification_results
    
    def extract_task_steps(self, text: str) -> List[str]:
        """Extract task steps from text to create a structured task list.
        
        Args:
            text: Text to extract task steps from
            
        Returns:
            List of task steps
        """
        steps = []
        
        # Try to find numbered lists (1. Step one)
        numbered_pattern = r'(?:^|\n)(\d+\.\s+.+?)(?=\n\d+\.|$)'
        numbered_matches = re.finditer(numbered_pattern, text, re.MULTILINE | re.DOTALL)
        for match in numbered_matches:
            step = match.group(1).strip()
            # Clean up the step text
            step = re.sub(r'^\d+\.\s+', '', step)
            steps.append(step)
        
        # If we didn't find numbered steps, try bullet points
        if not steps:
            bullet_pattern = r'(?:^|\n)([*\-•]\s+.+?)(?=\n[*\-•]|$)'
            bullet_matches = re.finditer(bullet_pattern, text, re.MULTILINE | re.DOTALL)
            for match in bullet_matches:
                step = match.group(1).strip()
                # Clean up the step text
                step = re.sub(r'^[*\-•]\s+', '', step)
                steps.append(step)
        
        # If we still don't have steps, try to split by sentences
        if not steps and "I'll" in text and "first" in text:
            # Look for sentences that might be describing steps
            step_pattern = r'(?:I\'ll|I will|Let me|I\'m going to)\s+(.+?)(?=\.|$)'
            step_matches = re.finditer(step_pattern, text)
            for match in step_matches:
                step = match.group(1).strip()
                if len(step) > 10:  # Avoid very short matches
                    steps.append(step)
        
        return steps
