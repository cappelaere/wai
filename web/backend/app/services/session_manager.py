"""
Session Management for Copilot Sessions.

This module provides the SessionManager class for managing user sessions,
conversation history, and contextual data for the scholarship copilot.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manager for user sessions, conversation history, and context.

    Provides in-memory session storage for MVP. Stores session data including:
    - User identification
    - Conversation history
    - Session context (current application, preferences, etc.)
    - Timestamps for creation and last access

    In production, this can be replaced with SQLite/PostgreSQL backend.

    Attributes:
        sessions: Dictionary mapping session_id to session data
        session_timeout: Timeout in seconds for session expiration
    """

    def __init__(self, session_timeout: Optional[int] = None):
        """
        Initialize the session manager.

        Args:
            session_timeout: Session timeout in seconds. Defaults to settings.session_timeout
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout or settings.session_timeout

        logger.info(f"Initialized SessionManager with timeout: {self.session_timeout}s")

    async def create_session(self, user_id: str) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Newly created session ID (UUID)

        Example:
            >>> session_id = await manager.create_session("user123")
            >>> print(session_id)
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        self.sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "context": {
                "current_application": None,
                "preferences": {},
            },
            "history": [],
            "created_at": now,
            "last_accessed": now,
        }

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    async def load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load session data by session ID.

        Updates last_accessed timestamp and returns session data.

        Args:
            session_id: Session identifier to load

        Returns:
            Dictionary containing session data with keys:
            - id: Session ID
            - user_id: User identifier
            - context: Session context dictionary
            - history: Conversation history list
            - created_at: Datetime of session creation
            - last_accessed: Datetime of last access

        Raises:
            ValueError: If session not found or expired

        Example:
            >>> session = await manager.load_session(session_id)
            >>> print(session["user_id"])
            'user123'
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        # Check if session is expired
        last_accessed = session["last_accessed"]
        timeout_delta = timedelta(seconds=self.session_timeout)
        if datetime.utcnow() - last_accessed > timeout_delta:
            logger.warning(f"Session {session_id} expired")
            await self.delete_session(session_id)
            raise ValueError(f"Session {session_id} has expired")

        # Update last accessed time
        session["last_accessed"] = datetime.utcnow()

        logger.debug(f"Loaded session {session_id}")
        return session

    async def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Save/update session data.

        Args:
            session_id: Session identifier to update
            data: Dictionary containing session data to save

        Returns:
            True if session was saved successfully

        Raises:
            ValueError: If session not found

        Example:
            >>> session_data = {
            ...     "context": {"current_application": "app123"},
            ...     "history": [...]
            ... }
            >>> await manager.save_session(session_id, session_data)
            True
        """
        if session_id not in self.sessions:
            logger.warning(f"Cannot save session {session_id}: not found")
            raise ValueError(f"Session {session_id} not found")

        # Update session data while preserving timestamps
        session = self.sessions[session_id]
        created_at = session["created_at"]
        user_id = session["user_id"]

        # Update with new data
        session.update(data)

        # Ensure critical fields are preserved
        session["id"] = session_id
        session["user_id"] = user_id
        session["created_at"] = created_at
        session["last_accessed"] = datetime.utcnow()

        logger.debug(f"Saved session {session_id}")
        return True

    async def update_context(self, session_id: str, key: str, value: Any) -> bool:
        """
        Update a specific context key for a session.

        Args:
            session_id: Session identifier
            key: Context key to update
            value: New value for the context key

        Returns:
            True if context was updated successfully

        Raises:
            ValueError: If session not found

        Example:
            >>> await manager.update_context(session_id, "current_application", "app123")
            True
        """
        session = await self.load_session(session_id)
        session["context"][key] = value
        session["last_accessed"] = datetime.utcnow()

        logger.debug(f"Updated context key '{key}' for session {session_id}")
        return True

    async def get_context(self, session_id: str, key: str) -> Any:
        """
        Get a specific context value from a session.

        Args:
            session_id: Session identifier
            key: Context key to retrieve

        Returns:
            Value of the context key, or None if not found

        Raises:
            ValueError: If session not found

        Example:
            >>> current_app = await manager.get_context(session_id, "current_application")
            >>> print(current_app)
            'app123'
        """
        session = await self.load_session(session_id)
        value = session["context"].get(key)

        logger.debug(f"Retrieved context key '{key}' for session {session_id}: {value}")
        return value

    async def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to the conversation history.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            True if message was added successfully

        Raises:
            ValueError: If session not found or invalid role

        Example:
            >>> await manager.add_message(session_id, "user", "What are the top candidates?")
            True
            >>> await manager.add_message(session_id, "assistant", "Based on the data...")
            True
        """
        if role not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

        session = await self.load_session(session_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }

        session["history"].append(message)
        session["last_accessed"] = datetime.utcnow()

        logger.debug(f"Added {role} message to session {session_id}")
        return True

    async def get_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Returns the most recent messages up to the specified limit.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return (default: 10)

        Returns:
            List of message dictionaries with keys:
            - role: 'user' or 'assistant'
            - content: Message text
            - timestamp: When the message was created

        Raises:
            ValueError: If session not found

        Example:
            >>> messages = await manager.get_messages(session_id, limit=5)
            >>> for msg in messages:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        session = await self.load_session(session_id)
        history = session["history"]

        # Return most recent messages up to limit
        recent_messages = history[-limit:] if limit > 0 else history

        logger.debug(f"Retrieved {len(recent_messages)} messages for session {session_id}")
        return recent_messages

    async def add_interaction(
        self,
        session_id: str,
        query: str,
        response: str
    ) -> bool:
        """
        Add a complete interaction (user query + assistant response) to history.

        Convenience method that adds both user and assistant messages.

        Args:
            session_id: Session identifier
            query: User's query
            response: Assistant's response

        Returns:
            True if interaction was added successfully

        Raises:
            ValueError: If session not found

        Example:
            >>> await manager.add_interaction(
            ...     session_id,
            ...     "Who are the top candidates?",
            ...     "Based on the data, the top 3 candidates are..."
            ... )
            True
        """
        await self.add_message(session_id, "user", query)
        await self.add_message(session_id, "assistant", response)

        logger.debug(f"Added interaction to session {session_id}")
        return True

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session data.

        Alias for load_session for compatibility with existing code.

        Args:
            session_id: Session identifier

        Returns:
            Complete session data dictionary

        Raises:
            ValueError: If session not found or expired
        """
        return await self.load_session(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if session was deleted, False if session didn't exist

        Example:
            >>> await manager.delete_session(session_id)
            True
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        else:
            logger.warning(f"Cannot delete session {session_id}: not found")
            return False

    async def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.

        Removes all sessions that haven't been accessed within the timeout period.

        Returns:
            Number of sessions deleted

        Example:
            >>> deleted_count = await manager.cleanup_expired()
            >>> print(f"Deleted {deleted_count} expired sessions")
        """
        now = datetime.utcnow()
        timeout_delta = timedelta(seconds=self.session_timeout)
        expired_sessions = []

        for session_id, session in self.sessions.items():
            last_accessed = session["last_accessed"]
            if now - last_accessed > timeout_delta:
                expired_sessions.append(session_id)

        # Delete expired sessions
        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        else:
            logger.debug("No expired sessions to clean up")

        return len(expired_sessions)

    def get_session_count(self) -> int:
        """
        Get the total number of active sessions.

        Returns:
            Number of sessions currently stored

        Example:
            >>> count = manager.get_session_count()
            >>> print(f"Active sessions: {count}")
        """
        return len(self.sessions)

    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all session IDs for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of session IDs belonging to the user

        Example:
            >>> sessions = manager.get_user_sessions("user123")
            >>> print(f"User has {len(sessions)} active sessions")
        """
        user_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session["user_id"] == user_id
        ]

        logger.debug(f"Found {len(user_sessions)} sessions for user {user_id}")
        return user_sessions
