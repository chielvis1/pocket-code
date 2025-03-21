"""CLI interface for the AI Shell and Coding Agent."""

import cmd
import sys
import webbrowser
from pathlib import Path
from typing import Optional
import json
import os

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()

class AgentCLI(cmd.Cmd):
    """Interactive CLI for the AI Shell and Coding Agent."""
    
    intro = """Welcome to PocketCode - Your AI Coding Assistant
Type /help or ? to list commands.
Type /login to configure your API key.
"""
    prompt = '> '
    
    def __init__(self):
        super().__init__()
        self.config_dir = Path.home() / '.pocketcode'
        self.config_file = self.config_dir / 'config.json'
        self.ensure_config_dir()
        self.load_config()
        
    def ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self.save_config({'api_key': None})
            
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file) as f:
                self.config = json.load(f)
        except Exception:
            self.config = {'api_key': None}
            
    def save_config(self, config):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        self.config = config

    def do_login(self, arg):
        """Configure API key for authentication."""
        console.print("\n[bold blue]API Key Configuration[/bold blue]")
        console.print("Opening browser to get your API key...")
        webbrowser.open('https://platform.openai.com/api-keys')
        
        api_key = console.input("\nPaste your API key here (input will be hidden): ", password=True)
        if api_key.strip():
            self.save_config({'api_key': api_key.strip()})
            console.print("[green]✓[/green] API key saved successfully!")
        else:
            console.print("[red]✗[/red] No API key provided.")

    def do_clear(self, arg):
        """Clear conversation history and free up context."""
        # TODO: Implement conversation history clearing
        console.print("[green]✓[/green] Conversation history cleared.")

    def do_compact(self, arg):
        """Clear conversation history but keep a summary in context."""
        # TODO: Implement conversation compacting
        console.print("[green]✓[/green] Conversation compacted with summary retained.")

    def do_config(self, arg):
        """Open config panel."""
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        # Mask API key
        api_key = self.config.get('api_key')
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "Not configured"
        
        table.add_row("API Key", masked_key)
        table.add_row("Working Directory", os.getcwd())
        
        console.print(table)

    def do_cost(self, arg):
        """Show the total cost and duration of the current session."""
        # TODO: Implement cost tracking
        console.print("Session Statistics:")
        console.print("Duration: 0h 0m 0s")
        console.print("Total Cost: $0.00")

    def do_doctor(self, arg):
        """Check the health of your installation."""
        table = Table(title="System Health Check")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        # Check API key
        api_status = "[green]✓[/green]" if self.config.get('api_key') else "[red]✗[/red]"
        table.add_row("API Key", api_status)
        
        # Check Python version
        import platform
        python_version = platform.python_version()
        python_status = "[green]✓[/green]" if python_version >= "3.8" else "[red]✗[/red]"
        table.add_row("Python Version", f"{python_status} ({python_version})")
        
        console.print(table)

    def do_exit(self, arg):
        """Exit the REPL."""
        console.print("\nGoodbye! 👋")
        return True

    def do_help(self, arg):
        """Show help and available commands."""
        help_text = {
            "Basic Commands": {
                "/login": "Configure your API key",
                "/help": "Show this help message",
                "/exit": "Exit the program",
            },
            "Session Management": {
                "/clear": "Clear conversation history",
                "/compact": "Clear history but keep summary",
                "/cost": "Show session cost and duration",
            },
            "Configuration": {
                "/config": "Show configuration panel",
                "/doctor": "Check system health",
            }
        }
        
        for section, commands in help_text.items():
            console.print(f"\n[bold blue]{section}[/bold blue]")
            table = Table(show_header=False)
            table.add_column(style="cyan")
            table.add_column(style="white")
            
            for cmd, desc in commands.items():
                table.add_row(cmd, desc)
            
            console.print(table)

    def default(self, line):
        """Handle natural language requests."""
        if not self.config.get('api_key'):
            console.print("[red]Error:[/red] Please configure your API key first using /login")
            return
            
        if line.startswith('/'):
            console.print(f"[red]Error:[/red] Unknown command: {line}")
            console.print("Type /help to see available commands.")
            return
            
        # TODO: Process natural language request through the agent
        console.print(f"Processing request: {line}")

def main():
    """Main entry point for the CLI."""
    try:
        AgentCLI().cmdloop()
    except KeyboardInterrupt:
        console.print("\nGoodbye! 👋")
        sys.exit(0)

if __name__ == '__main__':
    main() 