"""CLI interface for the AI agent."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from .agent import Agent

app = typer.Typer()
console = Console()

def get_history_file() -> Path:
    """Get the path to the history file."""
    config_dir = Path.home() / ".config" / "pocketcode"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "history"

class Interface:
    """CLI interface for interacting with the AI agent."""
    
    def __init__(self):
        """Initialize the interface."""
        self.agent: Optional[Agent] = None
        self.history_file = get_history_file()
        self.session = PromptSession(history=FileHistory(str(self.history_file)))
        
    def login(self) -> None:
        """Configure API key."""
        api_key = Prompt.ask("Enter your Anthropic API key")
        if not api_key.startswith("sk-"):
            console.print("[red]Invalid API key format. Should start with 'sk-'[/red]")
            return
            
        # Save API key securely
        config_dir = self.history_file.parent
        key_file = config_dir / "api_key"
        key_file.write_text(api_key)
        
        # Initialize agent in simulation mode by default
        self.agent = Agent(api_key, simulation_mode=True)
        console.print("[green]Successfully logged in![/green]")
        
    def load_api_key(self) -> Optional[str]:
        """Load saved API key."""
        key_file = self.history_file.parent / "api_key"
        if key_file.exists():
            return key_file.read_text().strip()
        return None
        
    def handle_command(self, command: str) -> bool:
        """Handle special commands."""
        if command == "/help":
            self.show_help()
            return True
        elif command == "/login":
            self.login()
            return True
        elif command == "/quit":
            return False
        elif command == "/clear":
            if self.agent:
                self.agent.clear_history()
            console.clear()
            return True
        elif command == "/direct":
            if self.agent:
                self.agent.simulation_mode = False
                console.print("[yellow]Switched to direct mode - commands will execute in your terminal[/yellow]")
            return True
        elif command == "/simulate":
            if self.agent:
                self.agent.simulation_mode = True
                console.print("[green]Switched to simulation mode - commands will be simulated[/green]")
            return True
        return False
        
    def show_help(self):
        """Show help message."""
        help_text = """
# Available Commands

- `/help`: Show this help message
- `/login`: Configure API key
- `/quit`: Exit the program
- `/clear`: Clear conversation history and screen
- `/direct`: Switch to direct mode (execute in your terminal)
- `/simulate`: Switch to simulation mode (safe testing)

In direct mode, commands will execute directly in your terminal.
In simulation mode, commands will be simulated (safe for testing).
"""
        console.print(Markdown(help_text))
        
    def run(self):
        """Run the CLI interface."""
        console.print("[bold]Welcome to PocketCode CLI![/bold]")
        console.print("Type /help for available commands")
        
        # Try to load saved API key
        api_key = self.load_api_key()
        if api_key:
            self.agent = Agent(api_key, simulation_mode=True)
            console.print("[green]Loaded saved API key[/green]")
        else:
            console.print("Please configure your API key with /login")
            
        while True:
            try:
                # Get user input
                user_input = self.session.prompt("> ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue
                    
                # Process request
                if not self.agent:
                    console.print("[red]Please configure your API key first with /login[/red]")
                    continue
                    
                # Show thinking indicator
                with console.status("Thinking...", spinner="dots"):
                    response = self.agent.process_request(user_input)
                    
                # Print response
                if response:
                    console.print(Markdown(response))
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {str(e)}")
                
        console.print("\nGoodbye! 👋")

def main():
    """Entry point for the CLI."""
    interface = Interface()
    interface.run()

if __name__ == "__main__":
    main() 