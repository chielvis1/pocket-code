import re
import os
from typing import List, Dict, Any, Optional, Tuple

class CommandExtractor:
    """Utility class to extract executable commands from task steps."""
    
    def __init__(self):
        """Initialize the command extractor."""
        # Patterns to match common command formats in task steps
        self.command_patterns = [
            # Match commands with $ prefix (most common in task steps)
            r'(?:^|\n)\s*\$\s+(.*?)(?=\n|$)',
            
            # Match commands with # or // comment followed by command on next line
            r'(?:^|\n)\s*(?:#|\/\/)[^\n]*?\n\s*(?!\$\s+)([a-z][a-zA-Z0-9_\-\.]*\s+.*?)(?=\n|$)',
            
            # Match commands that start with common CLI tools
            r'(?:^|\n)\s*(?:npm|yarn|npx|python|pip|docker|git|mkdir|cd|touch|cp|mv|rm|cat|echo|curl|wget)\s+.*?(?=\n|$)'
        ]
    
    def extract_commands_from_step(self, step_text: str) -> List[Dict[str, Any]]:
        """Extract executable commands from a task step.
        
        Args:
            step_text: The text of the task step
            
        Returns:
            List of dictionaries with command information
        """
        commands = []
        
        # Process each pattern
        for pattern in self.command_patterns:
            matches = re.finditer(pattern, step_text, re.MULTILINE)
            for match in matches:
                # Get the command text
                if match.groups():
                    # If we have a capture group, use that
                    cmd_text = match.group(1).strip()
                else:
                    # Otherwise use the whole match
                    cmd_text = match.group(0).strip()
                
                # Clean up the command text
                cmd_text = self._clean_command(cmd_text)
                
                # Skip if empty or already added
                if not cmd_text or any(c['command'] == cmd_text for c in commands):
                    continue
                
                # Add to our list
                commands.append({
                    'command': cmd_text,
                    'context': self._get_context(step_text, match.start(), match.end()),
                    'match': match.group(0)
                })
        
        return commands
    
    def _clean_command(self, cmd_text: str) -> str:
        """Clean up a command string.
        
        Args:
            cmd_text: The command text to clean
            
        Returns:
            Cleaned command text
        """
        # Remove $ prefix if present
        if cmd_text.startswith('$ '):
            cmd_text = cmd_text[2:].strip()
        
        # Remove any trailing comments
        cmd_text = re.sub(r'#.*$', '', cmd_text).strip()
        
        return cmd_text
    
    def _get_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around a match.
        
        Args:
            text: The full text
            start: Start position of the match
            end: End position of the match
            context_size: Number of characters of context to include
            
        Returns:
            Context string
        """
        # Get context before and after
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        
        # Extract context
        context = text[context_start:context_end]
        
        # Add ellipsis if needed
        if context_start > 0:
            context = '...' + context
        if context_end < len(text):
            context = context + '...'
        
        return context
