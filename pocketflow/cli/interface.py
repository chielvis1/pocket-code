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
Type /login to configure your Vertex AI credentials.
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
            self.save_config({
                'project_id': None,
                'location': None,
                'credentials_path': None
            })
            
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file) as f:
                self.config = json.load(f)
        except Exception:
            self.config = {
                'project_id': None,
                'location': None,
                'credentials_path': None
            }
            
    def save_config(self, config):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        self.config = config

    def do_login(self, arg):
        """Configure Vertex AI credentials for authentication."""
        console.print("\n[bold blue]Vertex AI Configuration[/bold blue]")
        console.print("\nPlease provide your Google Cloud credentials:")
        
        project_id = console.input("\nEnter your Google Cloud Project ID: ").strip()
        location = console.input("Enter your location (e.g., us-central1): ").strip()
        credentials_path = console.input("Enter the path to your service account key JSON file: ").strip()
        
        if project_id and location and credentials_path:
            if not os.path.exists(credentials_path):
                console.print("[red]✗[/red] Credentials file not found!")
                return
                
            self.save_config({
                'project_id': project_id,
                'location': location,
                'credentials_path': credentials_path
            })
            console.print("[green]✓[/green] Vertex AI credentials saved successfully!")
            
            # Set environment variable for credentials
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        else:
            console.print("[red]✗[/red] All fields are required.")

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
        
        table.add_row("Project ID", self.config.get('project_id') or "Not configured")
        table.add_row("Location", self.config.get('location') or "Not configured")
        table.add_row("Credentials", self.config.get('credentials_path') or "Not configured")
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
        
        # Check Vertex AI credentials
        creds_status = "[green]✓[/green]" if all([
            self.config.get('project_id'),
            self.config.get('location'),
            self.config.get('credentials_path')
        ]) else "[red]✗[/red]"
        table.add_row("Vertex AI Credentials", creds_status)
        
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
                "/login": "Configure your Vertex AI credentials",
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
        if not all([
            self.config.get('project_id'),
            self.config.get('location'),
            self.config.get('credentials_path')
        ]):
            console.print("[red]Error:[/red] Please configure your Vertex AI credentials first using /login")
            return
            
        if line.startswith('/'):
            console.print(f"[red]Error:[/red] Unknown command: {line}")
            console.print("Type /help to see available commands.")
            return
            
        # TODO: Process natural language request through the Vertex AI agent
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