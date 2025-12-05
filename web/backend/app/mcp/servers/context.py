"""Context MCP Server.

This server provides tools for managing conversation context and session state.
It maintains in-memory storage for session data, focused applications, and
other contextual information needed across copilot interactions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..servers.base import MCPServer, ToolSchema
from ..tools.schemas import (
    GET_CONTEXT_SCHEMA,
    UPDATE_CONTEXT_SCHEMA,
)

logger = logging.getLogger(__name__)


class ContextMCPServer(MCPServer):
    """MCP Server for managing conversation context and session state.

    This server provides tools to:
    - Store and retrieve session-specific context data
    - Track the currently focused application
    - Maintain conversation history and state
    - Manage user preferences and settings

    For this MVP, data is stored in-memory. In production, this could
    be backed by a database or cache like Redis.
    """

    def __init__(self):
        """Initialize the Context MCP Server."""
        super().__init__(
            name="context",
            description="Manage conversation context and session state"
        )
        # In-memory storage: {session_id: {context_data}}
        self._contexts: Dict[str, Dict[str, Any]] = {}
        # Track current application per session: {session_id: application_id}
        self._current_applications: Dict[str, str] = {}
        # Metadata for contexts: {session_id: {created_at, updated_at}}
        self._metadata: Dict[str, Dict[str, str]] = {}

    async def initialize(self) -> None:
        """Initialize the server and register tools."""
        # Helper function to convert schema from camelCase to snake_case keys
        def convert_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "name": schema["name"],
                "description": schema["description"],
                "input_schema": schema["inputSchema"],
                "return_schema": schema["returnSchema"]
            }

        # Register get_context tool
        self.register_tool(
            ToolSchema(**convert_schema(GET_CONTEXT_SCHEMA)),
            self._get_context
        )

        # Register update_context tool
        self.register_tool(
            ToolSchema(**convert_schema(UPDATE_CONTEXT_SCHEMA)),
            self._update_context
        )

        # Register custom tools for application focus
        self.register_tool(
            ToolSchema(
                name="get_current_application",
                description="Get the currently focused application for a session",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier"
                        }
                    },
                    "required": ["session_id"]
                },
                return_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "application_id": {"type": ["string", "null"]}
                    }
                }
            ),
            self._get_current_application
        )

        self.register_tool(
            ToolSchema(
                name="set_current_application",
                description="Set the currently focused application for a session",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier"
                        },
                        "application_id": {
                            "type": "string",
                            "description": "Application ID to focus on"
                        }
                    },
                    "required": ["session_id", "application_id"]
                },
                return_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "application_id": {"type": "string"},
                        "updated": {"type": "boolean"}
                    }
                }
            ),
            self._set_current_application
        )

        logger.info("Context MCP Server initialized with 4 tools")

    def _ensure_session_exists(self, session_id: str) -> None:
        """Ensure a session exists in storage, creating it if needed.

        Args:
            session_id: Session identifier
        """
        if session_id not in self._contexts:
            now = datetime.now().isoformat()
            self._contexts[session_id] = {}
            self._metadata[session_id] = {
                "created_at": now,
                "updated_at": now
            }
            logger.info(f"Created new session: {session_id}")

    async def _get_context(
        self,
        session_id: str,
        context_type: str = "conversation"
    ) -> Dict[str, Any]:
        """Retrieve context data for a session.

        Args:
            session_id: Session identifier
            context_type: Type of context to retrieve (conversation, application, user)

        Returns:
            Dictionary containing context data

        Raises:
            RuntimeError: If context retrieval fails
        """
        logger.info(f"Getting context for session {session_id} (type: {context_type})")

        self._ensure_session_exists(session_id)

        # Get context data (or empty dict if none exists)
        context_data = self._contexts.get(session_id, {})

        # Filter by context_type if specified
        if context_type != "conversation":
            # For specific types, return nested data
            context_data = context_data.get(context_type, {})

        metadata = self._metadata.get(session_id, {})

        result = {
            "session_id": session_id,
            "context_type": context_type,
            "data": context_data,
            "created_at": metadata.get("created_at", datetime.now().isoformat()),
            "updated_at": metadata.get("updated_at", datetime.now().isoformat())
        }

        logger.debug(f"Retrieved context for {session_id}: {len(context_data)} keys")
        return result

    async def _update_context(
        self,
        session_id: str,
        context_data: Dict[str, Any],
        merge: bool = True
    ) -> Dict[str, Any]:
        """Update or create context for a session.

        Args:
            session_id: Session identifier
            context_data: Context data to store
            merge: Whether to merge with existing context or replace it

        Returns:
            Dictionary confirming the update

        Raises:
            RuntimeError: If context update fails
        """
        logger.info(f"Updating context for session {session_id} (merge: {merge})")

        self._ensure_session_exists(session_id)

        # Update context data
        if merge:
            # Merge with existing data
            self._contexts[session_id].update(context_data)
        else:
            # Replace existing data
            self._contexts[session_id] = context_data.copy()

        # Update metadata
        self._metadata[session_id]["updated_at"] = datetime.now().isoformat()

        logger.debug(f"Updated context for {session_id}: {len(self._contexts[session_id])} keys")

        return {
            "session_id": session_id,
            "updated": True,
            "updated_at": self._metadata[session_id]["updated_at"]
        }

    async def _get_current_application(self, session_id: str) -> Dict[str, Any]:
        """Get the currently focused application for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session_id and application_id (or None)
        """
        logger.info(f"Getting current application for session {session_id}")

        self._ensure_session_exists(session_id)

        application_id = self._current_applications.get(session_id)

        result = {
            "session_id": session_id,
            "application_id": application_id
        }

        logger.debug(f"Current application for {session_id}: {application_id}")
        return result

    async def _set_current_application(
        self,
        session_id: str,
        application_id: str
    ) -> Dict[str, Any]:
        """Set the currently focused application for a session.

        Args:
            session_id: Session identifier
            application_id: Application ID to focus on

        Returns:
            Dictionary confirming the update
        """
        logger.info(f"Setting current application for session {session_id}: {application_id}")

        self._ensure_session_exists(session_id)

        # Set the current application
        self._current_applications[session_id] = application_id

        # Also store in general context for easy access
        if session_id in self._contexts:
            self._contexts[session_id]["current_application_id"] = application_id

        # Update metadata
        if session_id in self._metadata:
            self._metadata[session_id]["updated_at"] = datetime.now().isoformat()

        result = {
            "session_id": session_id,
            "application_id": application_id,
            "updated": True
        }

        logger.debug(f"Set current application for {session_id} to {application_id}")
        return result

    def clear_session(self, session_id: str) -> bool:
        """Clear all data for a session.

        This is a helper method for cleanup, not exposed as a tool.

        Args:
            session_id: Session identifier

        Returns:
            True if session was cleared, False if it didn't exist
        """
        if session_id in self._contexts:
            del self._contexts[session_id]
            self._current_applications.pop(session_id, None)
            self._metadata.pop(session_id, None)
            logger.info(f"Cleared session: {session_id}")
            return True
        return False

    def get_all_sessions(self) -> list[str]:
        """Get all active session IDs.

        This is a helper method for debugging/monitoring.

        Returns:
            List of session IDs
        """
        return list(self._contexts.keys())

    def get_session_count(self) -> int:
        """Get the number of active sessions.

        This is a helper method for monitoring.

        Returns:
            Number of active sessions
        """
        return len(self._contexts)
