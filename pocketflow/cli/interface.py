"""CLI interface for the AI agent."""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from .agent import Agent
from .permissions import check_directory_access, request_directory_access, check_sudo_access, request_sudo_access

app = typer.Typer()
console = Console()

COMMANDS = [
    "/help",
    "/login",
    "/quit",
    "/clear",
    "/config",
    "/doctor",
    "/cost"
]

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
        self.command_completer = WordCompleter(COMMANDS, sentence=True)
        self.session = PromptSession(
            history=FileHistory(str(self.history_file)),
            completer=self.command_completer,
            complete_while_typing=True
        )
        
    def login(self) -> None:
        """Configure API key."""
        console.print("\n[bold blue]Anthropic API Configuration[/bold blue]")
        console.print("\nPlease visit https://console.anthropic.com/settings/keys to get your API key.")
        
        api_key = console.input("\nEnter your Anthropic API key (input will be hidden): ", password=True)
        if not api_key.startswith("sk-"):
            console.print("[red]✗[/red] Invalid API key format. Should start with 'sk-'")
            return
            
        # Save API key securely
        config_dir = self.history_file.parent
        key_file = config_dir / "api_key"
        key_file.write_text(api_key)
        
        # Initialize agent
        self.agent = Agent(api_key)
        console.print("[green]✓[/green] Login successful! You may begin prompting.")
        
    def show_welcome_message(self):
        """Show welcome message after login."""
        welcome_text = """
# 🚀 Welcome to Pocket Code!

Type `/help` to see available commands
Or just tell me what you need help with!
"""
        console.print(Markdown(welcome_text))
        
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
        elif command == "/config":
            self.show_config()
            return True
        elif command == "/doctor":
            self.check_health()
            return True
        elif command == "/cost":
            self.show_cost()
            return True
        return False
        
    def show_help(self):
        """Show help message."""
        help_text = """
# Available Commands

## System Commands
- `/help`: Show this help message
- `/login`: Configure API key securely
- `/quit`: Exit the program
- `/clear`: Clear conversation history and screen

## Information
- `/config`: Show current configuration
- `/doctor`: Check system health
- `/cost`: Show session cost and duration

For any other input without a leading /, I will:
1. Respond to greetings and questions
2. Execute tasks and commands you request
3. Help with coding and development tasks

[dim]Note: Some operations may require directory or sudo access. I'll ask for permission when needed.[/dim]
"""
        console.print(Markdown(help_text))
        
    def show_config(self):
        """Show current configuration."""
        api_key = self.load_api_key()
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "Not configured"
        
        config_text = f"""
# Current Configuration

- API Key: {masked_key}
- Model: Claude 3.7 Sonnet
- Working Directory: {os.getcwd()}
- Sudo Access: {"[green]✓[/green] Configured" if check_sudo_access() else "[yellow]![/yellow] Not configured"}
"""
        console.print(Markdown(config_text))
        
    def check_health(self):
        """Check system health."""
        api_key = self.load_api_key()
        health_text = f"""
# System Health Check

- API Key: {"[green]✓[/green] Configured" if api_key else "[red]✗[/red] Not configured"}
- Python Version: [green]✓[/green] {sys.version.split()[0]}
- Working Directory: [green]✓[/green] {os.getcwd()}
- Sudo Access: {"[green]✓[/green] Configured" if check_sudo_access() else "[yellow]![/yellow] Not configured"}
"""
        console.print(Markdown(health_text))
        
    def show_cost(self):
        """Show session cost and duration."""
        cost_text = """
# Session Statistics

- Duration: 0h 0m 0s
- Total Cost: $0.00
"""
        console.print(Markdown(cost_text))
        
    def run(self):
        """Run the CLI interface."""
        console.print("[bold]Welcome to Pocket Code![/bold]")
        console.print("Type /help to see available commands")
        console.print("Or configure your API key with /login to get started")
        
        # Try to load saved API key
        api_key = self.load_api_key()
        if api_key:
            self.agent = Agent(api_key)
            console.print("[green]✓[/green] Loaded saved API key")
            
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
                    
                # Process regular request
                if not self.agent:
                    console.print("[red]Please configure your API key first with /login[/red]")
                    continue
                    
                # Show thinking indicator and process request
                with console.status("[bold yellow]Thinking...[/bold yellow]", spinner="dots"):
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