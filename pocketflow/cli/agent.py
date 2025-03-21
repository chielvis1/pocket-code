"""AI Agent implementation using Anthropic's Claude."""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict

from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown

console = Console()

class Agent:
    """AI Agent powered by Claude 3.7 Sonnet."""
    
    def __init__(self, api_key: str):
        """Initialize the agent with API key."""
        self.client = Anthropic(api_key=api_key)
        self.conversation_history: List[Dict] = []
        self.system_prompt = """You are a powerful agentic AI coding assistant, powered by Claude 3.7 Sonnet.
You operate in a command-line interface to help users with coding tasks.

Your capabilities include:
1. Understanding and executing shell commands
2. Reading, writing, and modifying code files
3. Searching codebases and documentation
4. Providing code suggestions and explanations
5. Debugging and troubleshooting

Please format your responses in markdown and be concise unless asked for details.
"""
    
    def process_request(self, request: str) -> str:
        """Process a user request through Claude."""
        try:
            # Create message with conversation history
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                }
            ]
            
            # Add conversation history
            for msg in self.conversation_history[-5:]:  # Keep last 5 messages for context
                messages.append(msg)
            
            # Add user's request
            messages.append({
                "role": "user",
                "content": request
            })
            
            # Get response from Claude
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=messages,
                temperature=0.7
            )
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": request
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content[0].text
            })
            
            return response.content[0].text
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def compact_history(self):
        """Compact history by summarizing old messages."""
        if len(self.conversation_history) <= 6:  # Keep if small
            return
            
        # Summarize old messages
        old_messages = self.conversation_history[:-6]  # All except last 6
        summary_request = "Please summarize our conversation so far very concisely."
        
        try:
            summary = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": "Please summarize the following conversation very concisely."},
                    *old_messages
                ],
                temperature=0.7
            )
            
            # Keep summary and last 6 messages
            self.conversation_history = [
                {"role": "assistant", "content": f"Previous conversation summary: {summary.content[0].text}"},
                *self.conversation_history[-6:]
            ]
        except Exception as e:
            console.print(f"[red]Error summarizing history:[/red] {str(e)}") 