from typing import Dict, Any, List, Optional
import logging
import os
import shutil

logger = logging.getLogger('ShellAgent')

class FileOperator:
    """Utility for file operations"""
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """Read file content"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            return {
                "content": content,
                "size": os.path.getsize(filepath),
                "modified": os.path.getmtime(filepath)
            }
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return {"error": str(e)}

    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            return {
                "success": True,
                "size": os.path.getsize(filepath)
            }
        except Exception as e:
            logger.error(f"Error writing file {filepath}: {str(e)}")
            return {"error": str(e)}

    def list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents"""
        try:
            items = os.listdir(path)
            return {
                "files": [f for f in items if os.path.isfile(os.path.join(path, f))],
                "directories": [d for d in items if os.path.isdir(os.path.join(path, d))]
            }
        except Exception as e:
            logger.error(f"Error listing directory {path}: {str(e)}")
            return {"error": str(e)}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory"""
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            return {"error": str(e)}

    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """Delete file"""
        try:
            os.remove(filepath)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {str(e)}")
            return {"error": str(e)}

    def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Move file"""
        try:
            shutil.move(src, dst)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error moving file {src} to {dst}: {str(e)}")
            return {"error": str(e)}

    def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Copy file"""
        try:
            shutil.copy2(src, dst)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error copying file {src} to {dst}: {str(e)}")
            return {"error": str(e)}

    def log_operation(self, operation: str, result: Dict[str, Any]) -> None:
        logger.debug(f"Logging {operation} operation: {result}") 