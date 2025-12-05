"""Base MCP server implementation.

This module provides the abstract base class for MCP (Model Context Protocol) servers.
MCP servers expose tools that can be called by AI models to perform specific tasks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)


class ToolSchema:
    """Schema definition for an MCP tool.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        input_schema: JSON schema defining the tool's input parameters
        return_schema: JSON schema defining the tool's return value structure
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        return_schema: Dict[str, Any]
    ):
        """Initialize a tool schema.

        Args:
            name: Unique identifier for the tool
            description: Human-readable description of what the tool does
            input_schema: JSON schema defining the tool's input parameters
            return_schema: JSON schema defining the tool's return value structure

        Raises:
            ValueError: If name or description is empty
        """
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Tool description must be a non-empty string")
        if not isinstance(input_schema, dict):
            raise ValueError("input_schema must be a dictionary")
        if not isinstance(return_schema, dict):
            raise ValueError("return_schema must be a dictionary")

        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.return_schema = return_schema

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool schema to dictionary representation.

        Returns:
            Dictionary containing the tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "returnSchema": self.return_schema
        }

    def __repr__(self) -> str:
        return f"ToolSchema(name={self.name!r})"


class MCPServer(ABC):
    """Abstract base class for MCP servers.

    MCP servers expose a collection of tools that can be called to perform
    specific tasks. Subclasses must implement the abstract methods to provide
    the actual tool implementations.

    Attributes:
        name: Unique identifier for this server
        description: Human-readable description of the server's purpose
    """

    def __init__(self, name: str, description: str):
        """Initialize the MCP server.

        Args:
            name: Unique identifier for this server
            description: Human-readable description of the server's purpose

        Raises:
            ValueError: If name or description is empty
        """
        if not name or not isinstance(name, str):
            raise ValueError("Server name must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Server description must be a non-empty string")

        self.name = name
        self.description = description
        self._tools: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self._initialized = False

        logger.info(f"Initialized MCP server: {name}")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the server and register its tools.

        This method should call register_tool() for each tool the server provides.
        Subclasses must implement this method to set up their specific tools.

        Raises:
            RuntimeError: If initialization fails
        """
        pass

    async def _ensure_initialized(self) -> None:
        """Ensure the server has been initialized.

        Raises:
            RuntimeError: If the server is not initialized
        """
        if not self._initialized:
            await self.initialize()
            self._initialized = True
        # If already initialized, do nothing (no-op)

    def register_tool(
        self,
        schema: ToolSchema,
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a tool with this server.

        Args:
            schema: Schema defining the tool's interface
            handler: Async function that implements the tool's logic

        Raises:
            ValueError: If a tool with the same name is already registered
            TypeError: If handler is not callable
        """
        if schema.name in self._tools:
            raise ValueError(
                f"Tool '{schema.name}' is already registered in server '{self.name}'"
            )

        if not callable(handler):
            raise TypeError(f"Handler for tool '{schema.name}' must be callable")

        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

        logger.debug(f"Registered tool '{schema.name}' in server '{self.name}'")

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Handle a tool call request.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result from the tool execution

        Raises:
            ValueError: If the tool is not found
            RuntimeError: If tool execution fails
        """
        await self._ensure_initialized()

        if tool_name not in self._handlers:
            raise ValueError(
                f"Tool '{tool_name}' not found in server '{self.name}'. "
                f"Available tools: {list(self._tools.keys())}"
            )

        try:
            logger.info(
                f"Executing tool '{tool_name}' in server '{self.name}' "
                f"with arguments: {arguments}"
            )
            handler = self._handlers[tool_name]
            result = await handler(**arguments)
            logger.debug(f"Tool '{tool_name}' executed successfully")
            return result

        except TypeError as e:
            raise RuntimeError(
                f"Invalid arguments for tool '{tool_name}': {str(e)}"
            ) from e
        except Exception as e:
            logger.error(
                f"Error executing tool '{tool_name}' in server '{self.name}': {str(e)}"
            )
            raise RuntimeError(
                f"Tool execution failed for '{tool_name}': {str(e)}"
            ) from e

    async def get_tools(self) -> List[ToolSchema]:
        """Get all tools registered with this server.

        Returns:
            List of tool schemas
        """
        await self._ensure_initialized()
        return list(self._tools.values())

    def get_tool(self, tool_name: str) -> Optional[ToolSchema]:
        """Get a specific tool schema by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Tool schema if found, None otherwise
        """
        return self._tools.get(tool_name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, tools={len(self._tools)})"
