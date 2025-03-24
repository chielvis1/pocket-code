"""Enhanced context management for maintaining long-term conversation history."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

logger = logging.getLogger('ShellAgent')

class EnhancedContextManager:
    """Utility for managing and persisting conversation context."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the context manager with optional storage directory."""
        # Set default storage directory if not provided
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".pocket-code", "context")
        
        self.storage_dir = storage_dir
        self.db_path = os.path.join(storage_dir, "context.db")
        self.current_session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.conversation_history = []
        self.context_summary = ""
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Enhanced context manager initialized with storage at {storage_dir}")
    
    def _init_database(self):
        """Initialize the SQLite database for context storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                summary TEXT
            )
            ''')
            
            # Create messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                role TEXT,
                content TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
            
            # Create state table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                working_dir TEXT,
                env_vars TEXT,
                command_history TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
            
            # Insert new session
            cursor.execute('''
            INSERT INTO sessions (session_id, start_time, end_time, summary)
            VALUES (?, ?, NULL, ?)
            ''', (self.current_session_id, datetime.now().isoformat(), ""))
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history and persist it."""
        timestamp = datetime.now().isoformat()
        
        # Add to in-memory history
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        self.conversation_history.append(message)
        
        # Persist to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO messages (session_id, timestamp, role, content)
            VALUES (?, ?, ?, ?)
            ''', (self.current_session_id, timestamp, role, content))
            conn.commit()
            conn.close()
            logger.debug(f"Message from {role} persisted to database")
        except Exception as e:
            logger.error(f"Error persisting message: {str(e)}")
    
    def update_state(self, working_dir: str, env_vars: Dict[str, str], command_history: List[Dict[str, Any]]):
        """Update and persist the current state."""
        timestamp = datetime.now().isoformat()
        
        # Persist to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO state (session_id, timestamp, working_dir, env_vars, command_history)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                self.current_session_id,
                timestamp,
                working_dir,
                json.dumps(env_vars),
                json.dumps(command_history)
            ))
            conn.commit()
            conn.close()
            logger.debug("State updated and persisted to database")
        except Exception as e:
            logger.error(f"Error persisting state: {str(e)}")
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the conversation history, optionally limited to the last N messages."""
        if limit is not None and limit > 0:
            return self.conversation_history[-limit:]
        return self.conversation_history
    
    def get_full_context(self, max_messages: int = 50) -> Dict[str, Any]:
        """Get the full context including conversation history and state."""
        # Get the most recent state
        state = self._get_latest_state()
        
        # Get conversation history (limited to max_messages)
        history = self.get_conversation_history(max_messages)
        
        # Include summary if available
        context = {
            "conversation_history": history,
            "state": state,
            "summary": self.context_summary,
            "session_id": self.current_session_id
        }
        
        return context
    
    def _get_latest_state(self) -> Dict[str, Any]:
        """Get the latest state from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            SELECT working_dir, env_vars, command_history
            FROM state
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            ''', (self.current_session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "working_dir": row[0],
                    "env_vars": json.loads(row[1]),
                    "command_history": json.loads(row[2])
                }
            return {}
        except Exception as e:
            logger.error(f"Error retrieving latest state: {str(e)}")
            return {}
    
    def update_summary(self, summary: str):
        """Update the context summary."""
        self.context_summary = summary
        
        # Update in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE sessions
            SET summary = ?
            WHERE session_id = ?
            ''', (summary, self.current_session_id))
            conn.commit()
            conn.close()
            logger.debug("Context summary updated")
        except Exception as e:
            logger.error(f"Error updating summary: {str(e)}")
    
    def end_session(self):
        """Mark the current session as ended."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE sessions
            SET end_time = ?
            WHERE session_id = ?
            ''', (datetime.now().isoformat(), self.current_session_id))
            conn.commit()
            conn.close()
            logger.info(f"Session {self.current_session_id} marked as ended")
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
    
    def get_previous_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get information about previous sessions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
            SELECT session_id, start_time, end_time, summary
            FROM sessions
            WHERE session_id != ?
            ORDER BY start_time DESC
            LIMIT ?
            ''', (self.current_session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                sessions.append({
                    "session_id": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                    "summary": row[3]
                })
            
            return sessions
        except Exception as e:
            logger.error(f"Error retrieving previous sessions: {str(e)}")
            return []
    
    def load_session(self, session_id: str) -> bool:
        """Load a previous session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute('''
            SELECT session_id FROM sessions
            WHERE session_id = ?
            ''', (session_id,))
            
            if not cursor.fetchone():
                logger.error(f"Session {session_id} not found")
                conn.close()
                return False
            
            # Load messages
            cursor.execute('''
            SELECT timestamp, role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp
            ''', (session_id,))
            
            messages = cursor.fetchall()
            self.conversation_history = [
                {"timestamp": msg[0], "role": msg[1], "content": msg[2]}
                for msg in messages
            ]
            
            # Load summary
            cursor.execute('''
            SELECT summary FROM sessions
            WHERE session_id = ?
            ''', (session_id,))
            
            summary = cursor.fetchone()
            if summary:
                self.context_summary = summary[0]
            
            conn.close()
            
            self.current_session_id = session_id
            logger.info(f"Session {session_id} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return False
    
    def generate_summary(self, model_function) -> str:
        """Generate a summary of the current conversation using the provided model function."""
        # Get the last 20 messages or all if less
        messages = self.get_conversation_history(20)
        
        if not messages:
            return "No conversation history to summarize."
        
        # Format messages for summarization
        formatted_messages = []
        for msg in messages:
            formatted_messages.append(f"{msg['role'].upper()}: {msg['content']}")
        
        conversation_text = "\n\n".join(formatted_messages)
        
        # Use the provided model function to generate a summary
        prompt = f"""Please provide a concise summary (max 200 words) of the following conversation, 
focusing on the main topics discussed, key decisions made, and any important information that should be remembered.

CONVERSATION:
{conversation_text}

SUMMARY:"""
        
        try:
            summary = model_function(prompt)
            self.update_summary(summary)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Failed to generate summary."
