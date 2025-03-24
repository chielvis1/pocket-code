"""Task manager for creating and tracking task lists to prevent hallucinations."""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('ShellAgent')

class TaskManager:
    """Utility for creating and tracking task lists to ground agent responses."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the task manager with optional storage directory."""
        # Set default storage directory if not provided
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".pocket-code", "tasks")
        
        self.storage_dir = storage_dir
        self.current_task_id = None
        self.current_task = None
        self.task_history = []
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        logger.info(f"Task manager initialized with storage at {storage_dir}")
    
    def create_task(self, request: str, task_steps: List[str]) -> str:
        """Create a new task with steps and return its ID.
        
        Args:
            request: The original user request
            task_steps: List of steps to complete the task
            
        Returns:
            Task ID
        """
        # Generate a unique task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create task structure
        task = {
            "id": task_id,
            "request": request,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": [{"description": step, "status": "pending", "output": None} for step in task_steps],
            "current_step_index": 0,
            "error_count": 0,
            "completion_percentage": 0
        }
        
        # Save the task
        self._save_task(task)
        
        # Set as current task
        self.current_task_id = task_id
        self.current_task = task
        
        # Add to history
        self.task_history.append(task_id)
        
        logger.info(f"Created task {task_id} with {len(task_steps)} steps")
        return task_id
    
    def update_step_status(self, step_index: int, status: str, output: Optional[str] = None) -> Dict[str, Any]:
        """Update the status of a task step.
        
        Args:
            step_index: Index of the step to update
            status: New status ('pending', 'in_progress', 'completed', 'error')
            output: Optional output from the step execution
            
        Returns:
            Updated task
        """
        if not self.current_task:
            logger.error("No current task to update")
            return {}
        
        # Validate step index
        if step_index < 0 or step_index >= len(self.current_task["steps"]):
            logger.error(f"Invalid step index: {step_index}")
            return self.current_task
        
        # Update step
        self.current_task["steps"][step_index]["status"] = status
        if output is not None:
            self.current_task["steps"][step_index]["output"] = output
        
        # Update task metadata
        self.current_task["updated_at"] = datetime.now().isoformat()
        
        # Update current step index if completed
        if status == "completed" and step_index == self.current_task["current_step_index"]:
            if step_index < len(self.current_task["steps"]) - 1:
                self.current_task["current_step_index"] = step_index + 1
        
        # Update error count
        if status == "error":
            self.current_task["error_count"] += 1
        
        # Update completion percentage
        completed_steps = sum(1 for step in self.current_task["steps"] if step["status"] == "completed")
        total_steps = len(self.current_task["steps"])
        self.current_task["completion_percentage"] = int((completed_steps / total_steps) * 100)
        
        # Update task status if all steps are completed
        if all(step["status"] == "completed" for step in self.current_task["steps"]):
            self.current_task["status"] = "completed"
        
        # Save updated task
        self._save_task(self.current_task)
        
        logger.info(f"Updated step {step_index} to status '{status}'")
        return self.current_task
    
    def get_current_task(self) -> Dict[str, Any]:
        """Get the current task.
        
        Returns:
            Current task or empty dict if none
        """
        return self.current_task or {}
    
    def get_current_step(self) -> Dict[str, Any]:
        """Get the current step of the current task.
        
        Returns:
            Current step or empty dict if none
        """
        if not self.current_task:
            return {}
        
        step_index = self.current_task["current_step_index"]
        if step_index < 0 or step_index >= len(self.current_task["steps"]):
            return {}
        
        return self.current_task["steps"][step_index]
    
    def add_step(self, description: str) -> Dict[str, Any]:
        """Add a new step to the current task.
        
        Args:
            description: Description of the new step
            
        Returns:
            Updated task
        """
        if not self.current_task:
            logger.error("No current task to update")
            return {}
        
        # Add new step
        self.current_task["steps"].append({
            "description": description,
            "status": "pending",
            "output": None
        })
        
        # Update task metadata
        self.current_task["updated_at"] = datetime.now().isoformat()
        
        # Save updated task
        self._save_task(self.current_task)
        
        logger.info(f"Added new step to task {self.current_task_id}")
        return self.current_task
    
    def complete_task(self, summary: Optional[str] = None) -> Dict[str, Any]:
        """Mark the current task as completed.
        
        Args:
            summary: Optional summary of task completion
            
        Returns:
            Completed task
        """
        if not self.current_task:
            logger.error("No current task to complete")
            return {}
        
        # Update task status
        self.current_task["status"] = "completed"
        self.current_task["updated_at"] = datetime.now().isoformat()
        self.current_task["completion_percentage"] = 100
        
        # Add summary if provided
        if summary:
            self.current_task["summary"] = summary
        
        # Save updated task
        self._save_task(self.current_task)
        
        logger.info(f"Completed task {self.current_task_id}")
        return self.current_task
    
    def get_task_progress(self) -> Dict[str, Any]:
        """Get progress information for the current task.
        
        Returns:
            Task progress information
        """
        if not self.current_task:
            return {
                "status": "no_task",
                "completion_percentage": 0,
                "current_step": None,
                "total_steps": 0,
                "completed_steps": 0
            }
        
        completed_steps = sum(1 for step in self.current_task["steps"] if step["status"] == "completed")
        
        return {
            "status": self.current_task["status"],
            "completion_percentage": self.current_task["completion_percentage"],
            "current_step": self.get_current_step().get("description", ""),
            "total_steps": len(self.current_task["steps"]),
            "completed_steps": completed_steps,
            "error_count": self.current_task["error_count"]
        }
    
    def format_task_list(self) -> str:
        """Format the current task list for display.
        
        Returns:
            Formatted task list as markdown
        """
        if not self.current_task:
            return "No active task."
        
        # Format task header
        result = f"# Task: {self.current_task['request']}\n\n"
        result += f"Progress: {self.current_task['completion_percentage']}% complete\n\n"
        
        # Format steps
        result += "## Steps:\n\n"
        for i, step in enumerate(self.current_task["steps"]):
            status_marker = "[ ]"
            if step["status"] == "completed":
                status_marker = "[x]"
            elif step["status"] == "in_progress":
                status_marker = "[→]"
            elif step["status"] == "error":
                status_marker = "[!]"
            
            result += f"{i+1}. {status_marker} {step['description']}\n"
            
            # Add output if available and not too long
            if step["output"] and len(step["output"]) < 500:
                result += f"   ```\n   {step['output']}\n   ```\n"
        
        return result
    
    def _save_task(self, task: Dict[str, Any]) -> None:
        """Save a task to disk.
        
        Args:
            task: Task to save
        """
        task_id = task["id"]
        task_path = os.path.join(self.storage_dir, f"{task_id}.json")
        
        try:
            with open(task_path, 'w') as f:
                json.dump(task, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving task {task_id}: {str(e)}")
    
    def load_task(self, task_id: str) -> Dict[str, Any]:
        """Load a task from disk.
        
        Args:
            task_id: ID of the task to load
            
        Returns:
            Loaded task or empty dict if not found
        """
        task_path = os.path.join(self.storage_dir, f"{task_id}.json")
        
        if not os.path.exists(task_path):
            logger.error(f"Task {task_id} not found")
            return {}
        
        try:
            with open(task_path, 'r') as f:
                task = json.load(f)
                
            # Set as current task
            self.current_task_id = task_id
            self.current_task = task
            
            logger.info(f"Loaded task {task_id}")
            return task
        except Exception as e:
            logger.error(f"Error loading task {task_id}: {str(e)}")
            return {}
