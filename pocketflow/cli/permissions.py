"""Permission handling utilities for PocketCode."""

import os
import subprocess
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

console = Console()

def check_directory_access(path: str) -> bool:
    """Check if we have access to a directory."""
    try:
        Path(path).resolve().stat()
        return True
    except PermissionError:
        return False

def request_directory_access(path: str) -> bool:
    """Request user permission to access a directory."""
    console.print(f"\n[yellow]⚠️  Permission required[/yellow]")
    console.print(f"PocketCode needs access to: {path}")
    return Confirm.ask("Would you like to grant access?")

def check_sudo_access() -> bool:
    """Check if we have sudo access."""
    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def request_sudo_access() -> bool:
    """Request user permission to configure sudo access."""
    console.print("\n[yellow]⚠️  Superuser access required[/yellow]")
    console.print("Some operations require superuser privileges.")
    if Confirm.ask("Would you like to configure sudo access for PocketCode?"):
        try:
            # Show visudo command that needs to be run
            console.print("\nPlease run this command to configure sudo access:")
            console.print("[blue]sudo visudo -f /etc/sudoers.d/pocketcode[/blue]")
            console.print("\nAnd add this line:")
            console.print("[green]%admin ALL=(ALL) NOPASSWD: /usr/local/bin/pcode[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error configuring sudo access:[/red] {str(e)}")
            return False
    return False 