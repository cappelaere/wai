"""Tool registry for MCP servers.

This module provides a centralized registry for managing MCP tools across
multiple servers. It allows tools to be registered, looked up, and tracked
by their server association.
"""

from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing MCP tools across multiple servers.

    The ToolRegistry maintains a mapping of tool names to their schemas and
    the servers that provide them. This allows for centralized tool discovery
    and routing of tool calls to the appropriate server.

    Attributes:
        _tools: Mapping of tool name to (server_name, tool_schema) tuple
        _server_tools: Mapping of server name to list of tool names
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        self._server_tools: Dict[str, List[str]] = {}
        logger.info("Initialized ToolRegistry")

    def register(
        self,
        server_name: str,
        tool_name: str,
        tool_schema: Dict[str, Any]
    ) -> None:
        """Register a tool with the registry.

        Args:
            server_name: Name of the server providing the tool
            tool_name: Name of the tool to register
            tool_schema: Schema definition for the tool

        Raises:
            ValueError: If the tool is already registered or if parameters are invalid
        """
        if not server_name or not isinstance(server_name, str):
            raise ValueError("server_name must be a non-empty string")
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("tool_name must be a non-empty string")
        if not isinstance(tool_schema, dict):
            raise ValueError("tool_schema must be a dictionary")

        if tool_name in self._tools:
            existing_server = self._tools[tool_name][0]
            raise ValueError(
                f"Tool '{tool_name}' is already registered by server '{existing_server}'. "
                f"Cannot register it again for server '{server_name}'."
            )

        # Validate tool schema has required fields
        required_fields = ["name", "description", "inputSchema", "returnSchema"]
        missing_fields = [field for field in required_fields if field not in tool_schema]
        if missing_fields:
            raise ValueError(
                f"tool_schema is missing required fields: {missing_fields}"
            )

        # Register the tool
        self._tools[tool_name] = (server_name, tool_schema)

        # Track which tools belong to which server
        if server_name not in self._server_tools:
            self._server_tools[server_name] = []
        self._server_tools[server_name].append(tool_name)

        logger.info(
            f"Registered tool '{tool_name}' for server '{server_name}'"
        )

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool from the registry.

        Args:
            tool_name: Name of the tool to unregister

        Raises:
            ValueError: If the tool is not registered
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' is not registered")

        server_name, _ = self._tools[tool_name]

        # Remove from tools mapping
        del self._tools[tool_name]

        # Remove from server tools list
        if server_name in self._server_tools:
            self._server_tools[server_name].remove(tool_name)
            if not self._server_tools[server_name]:
                del self._server_tools[server_name]

        logger.info(f"Unregistered tool '{tool_name}' from server '{server_name}'")

    def lookup(self, tool_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Look up a tool by name.

        Args:
            tool_name: Name of the tool to look up

        Returns:
            Tuple of (server_name, tool_schema) if found, None otherwise
        """
        return self._tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools.

        Returns:
            Dictionary mapping tool names to their schemas
        """
        return {
            tool_name: tool_schema
            for tool_name, (_, tool_schema) in self._tools.items()
        }

    def get_tools_by_server(self, server_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all tools provided by a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary mapping tool names to their schemas for the given server
        """
        if server_name not in self._server_tools:
            return {}

        return {
            tool_name: self._tools[tool_name][1]
            for tool_name in self._server_tools[server_name]
        }

    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Get the server name that provides a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Server name if the tool is found, None otherwise
        """
        result = self.lookup(tool_name)
        return result[0] if result else None

    def list_servers(self) -> List[str]:
        """List all servers that have registered tools.

        Returns:
            List of server names
        """
        return list(self._server_tools.keys())

    def list_tool_names(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def clear(self) -> None:
        """Clear all registered tools from the registry.

        This is useful for testing or resetting the registry state.
        """
        tool_count = len(self._tools)
        server_count = len(self._server_tools)
        self._tools.clear()
        self._server_tools.clear()
        logger.info(
            f"Cleared registry: removed {tool_count} tools from {server_count} servers"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry.

        Returns:
            Dictionary containing registry statistics
        """
        return {
            "total_tools": len(self._tools),
            "total_servers": len(self._server_tools),
            "tools_per_server": {
                server: len(tools)
                for server, tools in self._server_tools.items()
            }
        }

    def __len__(self) -> int:
        """Get the number of registered tools.

        Returns:
            Number of registered tools
        """
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if the tool is registered, False otherwise
        """
        return tool_name in self._tools

    def __repr__(self) -> str:
        return (
            f"ToolRegistry(tools={len(self._tools)}, "
            f"servers={len(self._server_tools)})"
        )
