import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .command_extractor import CommandExtractor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskManager")

class TaskManager:
    """Manages task lists and tracks progress through tasks."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the task manager.
        
        Args:
            storage_dir: Directory to store task data (defaults to ~/.pocketflow/tasks)
        """
        # Set up storage directory
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".pocketflow", "tasks")
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize state
        self.current_task_id = None
        self.command_extractor = CommandExtractor()
        
        # Load any active task
        self._load_active_task()
    
    def create_task(self, request: str, steps: List[str]) -> str:
        """Create a new task with the given steps.
        
        Args:
            request: The original user request
            steps: List of task steps
            
        Returns:
            Task ID
        """
        # Generate a unique ID for the task
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Process steps to extract commands
        processed_steps = []
        for i, step in enumerate(steps):
            # Extract commands from the step
            commands = self.command_extractor.extract_commands_from_step(step)
            
            # Create step object
            processed_steps.append({
                "index": i,
                "description": step,
                "status": "pending",
                "commands": commands,
                "output": None,
                "error": None
            })
        
        # Create task object
        task = {
            "id": task_id,
            "request": request,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": processed_steps,
            "current_step_index": 0
        }
        
        # Save task to disk
        self._save_task(task)
        
        # Set as current task
        self.current_task_id = task_id
        
        # Log task creation
        logger.info(f"Created task {task_id} with {len(steps)} steps")
        
        return task_id
    
    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """Get the current active task.
        
        Returns:
            Current task or None if no active task
        """
        if self.current_task_id is None:
            return None
        
        return self._load_task(self.current_task_id)
    
    def get_current_step(self) -> Optional[Dict[str, Any]]:
        """Get the current step of the active task.
        
        Returns:
            Current step or None if no active task or all steps completed
        """
        task = self.get_current_task()
        if task is None:
            return None
        
        current_index = task.get("current_step_index", 0)
        steps = task.get("steps", [])
        
        if current_index >= len(steps):
            return None
        
        return steps[current_index]
    
    def get_next_command(self) -> Optional[Dict[str, Any]]:
        """Get the next command to execute from the current step.
        
        Returns:
            Command information or None if no commands to execute
        """
        step = self.get_current_step()
        if step is None:
            return None
        
        # Find the first pending command
        commands = step.get("commands", [])
        for i, cmd in enumerate(commands):
            if "executed" not in cmd or not cmd["executed"]:
                return {
                    "step_index": step["index"],
                    "command_index": i,
                    "command": cmd["command"],
                    "context": cmd.get("context", "")
                }
        
        return None
    
    def update_step_status(self, step_index: int, status: str, output: Optional[str] = None) -> None:
        """Update the status of a step.
        
        Args:
            step_index: Index of the step to update
            status: New status (pending, in_progress, completed, error)
            output: Optional output from the step
        """
        task = self.get_current_task()
        if task is None:
            return
        
        # Update the step
        if 0 <= step_index < len(task["steps"]):
            task["steps"][step_index]["status"] = status
            if output is not None:
                task["steps"][step_index]["output"] = output
            
            # If this step is completed, move to the next step
            if status == "completed" and step_index == task["current_step_index"]:
                task["current_step_index"] = step_index + 1
            
            # If all steps are completed, mark the task as completed
            if task["current_step_index"] >= len(task["steps"]):
                task["status"] = "completed"
            
            # Update the task
            task["updated_at"] = datetime.now().isoformat()
            self._save_task(task)
    
    def update_command_status(self, step_index: int, command_index: int, executed: bool, output: Optional[str] = None, error: Optional[str] = None) -> None:
        """Update the status of a command.
        
        Args:
            step_index: Index of the step containing the command
            command_index: Index of the command within the step
            executed: Whether the command was executed
            output: Optional output from the command
            error: Optional error from the command
        """
        task = self.get_current_task()
        if task is None:
            return
        
        # Update the command
        if 0 <= step_index < len(task["steps"]):
            step = task["steps"][step_index]
            if 0 <= command_index < len(step.get("commands", [])):
                command = step["commands"][command_index]
                command["executed"] = executed
                if output is not None:
                    command["output"] = output
                if error is not None:
                    command["error"] = error
                
                # Update the task
                task["updated_at"] = datetime.now().isoformat()
                self._save_task(task)
    
    def advance_to_next_step(self) -> Optional[Dict[str, Any]]:
        """Advance to the next step in the current task.
        
        Returns:
            The next step or None if no more steps
        """
        task = self.get_current_task()
        if task is None:
            return None
        
        # Move to the next step
        current_index = task.get("current_step_index", 0)
        task["current_step_index"] = current_index + 1
        
        # Update the task
        task["updated_at"] = datetime.now().isoformat()
        self._save_task(task)
        
        # Return the next step
        return self.get_current_step()
    
    def complete_task(self) -> None:
        """Mark the current task as completed."""
        task = self.get_current_task()
        if task is None:
            return
        
        # Mark as completed
        task["status"] = "completed"
        task["updated_at"] = datetime.now().isoformat()
        self._save_task(task)
        
        # Clear current task
        self.current_task_id = None
    
    def format_task_list(self) -> str:
        """Format the current task as a markdown task list.
        
        Returns:
            Markdown formatted task list
        """
        task = self.get_current_task()
        if task is None:
            return "No active task"
        
        # Format the task list
        result = f"# Task List:\n\n"
        
        # Add each step
        for i, step in enumerate(task.get("steps", [])):
            status_marker = "✓" if step.get("status") == "completed" else "•"
            if i == task.get("current_step_index", 0):
                status_marker = "→"
            
            result += f"{i+1}. {status_marker} {step.get('description')}\n"
        
        # Add current step details
        current_step = self.get_current_step()
        if current_step:
            result += f"\n## Current Step: {current_step.get('description')}\n\n"
            
            # Add commands
            for cmd in current_step.get("commands", []):
                executed = cmd.get("executed", False)
                status = "✓" if executed else "•"
                result += f"- {status} `{cmd.get('command')}`\n"
                
                # Add output if available
                if executed and "output" in cmd:
                    result += f"  Output: ```\n{cmd.get('output')}\n```\n"
        
        return result
    
    def _save_task(self, task: Dict[str, Any]) -> None:
        """Save a task to disk.
        
        Args:
            task: Task to save
        """
        task_id = task["id"]
        task_path = os.path.join(self.storage_dir, f"{task_id}.json")
        
        with open(task_path, "w") as f:
            json.dump(task, f, indent=2)
        
        # Also save as active task if this is the current task
        if task_id == self.current_task_id:
            active_path = os.path.join(self.storage_dir, "active_task.json")
            with open(active_path, "w") as f:
                json.dump({"task_id": task_id}, f, indent=2)
    
    def _load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load a task from disk.
        
        Args:
            task_id: ID of the task to load
            
        Returns:
            Task or None if not found
        """
        task_path = os.path.join(self.storage_dir, f"{task_id}.json")
        
        if not os.path.exists(task_path):
            return None
        
        try:
            with open(task_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading task {task_id}: {str(e)}")
            return None
    
    def _load_active_task(self) -> None:
        """Load the active task if any."""
        active_path = os.path.join(self.storage_dir, "active_task.json")
        
        if not os.path.exists(active_path):
            return
        
        try:
            with open(active_path, "r") as f:
                active = json.load(f)
                self.current_task_id = active.get("task_id")
        except Exception as e:
            logger.error(f"Error loading active task: {str(e)}")
