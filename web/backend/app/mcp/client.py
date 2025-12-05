"""MCP Client Manager.

This module provides the MCPClientManager class which orchestrates all MCP servers
and handles tool calls from Claude. It serves as the central point for initializing
servers, registering tools, and routing tool calls to the appropriate server.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.mcp.servers.application_data import ApplicationDataMCPServer
from app.mcp.servers.analysis import AnalysisMCPServer
from app.mcp.servers.context import ContextMCPServer
from app.mcp.servers.processor import ProcessorMCPServer
from app.mcp.tools.registry import ToolRegistry
from app.mcp.servers.base import MCPServer

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manager for all MCP servers and tool orchestration.

    The MCPClientManager is responsible for:
    - Initializing all MCP servers
    - Maintaining a registry of all available tools
    - Routing tool calls to the appropriate server
    - Providing tool schemas to Claude API
    - Handling errors and returning formatted responses

    This class serves as the bridge between the FastAPI backend and the
    MCP server infrastructure, allowing Claude to interact with scholarship
    application data through a unified tool interface.

    Attributes:
        servers: Dictionary mapping server names to server instances
        registry: ToolRegistry for tracking all available tools
    """

    def __init__(self):
        """Initialize the MCP Client Manager.

        Creates an empty servers dictionary and tool registry.
        Server initialization happens asynchronously via initialize().
        """
        self.servers: Dict[str, MCPServer] = {}
        self.registry = ToolRegistry()
        logger.info("MCPClientManager created")

    async def initialize(self) -> None:
        """Initialize all MCP servers and register their tools.

        This method:
        1. Creates instances of all four MCP servers:
           - ApplicationDataMCPServer for accessing application data
           - AnalysisMCPServer for analyzing applications
           - ContextMCPServer for managing session state
           - ProcessorMCPServer for verifying processing status
        2. Calls initialize() on each server to register their tools
        3. Registers each server's tools in the central registry

        This method should be called once during application startup.

        Raises:
            RuntimeError: If server initialization fails
        """
        logger.info("Initializing MCP Client Manager")

        try:
            # Create server instances
            app_data_server = ApplicationDataMCPServer()
            # Pass the shared app_data_server instance to analysis_server
            analysis_server = AnalysisMCPServer(data_server=app_data_server)
            context_server = ContextMCPServer()
            processor_server = ProcessorMCPServer()

            # Store servers by name
            self.servers = {
                "application_data": app_data_server,
                "analysis": analysis_server,
                "context": context_server,
                "processor": processor_server,
            }

            # Initialize each server
            logger.info("Initializing servers...")
            for server_name, server in self.servers.items():
                logger.info(f"Initializing {server_name} server")
                await server.initialize()
                # Mark server as initialized to prevent _ensure_initialized from calling it again
                server._initialized = True

                # Register server's tools in the registry
                tools = await server.get_tools()
                for tool in tools:
                    tool_dict = tool.to_dict()
                    self.registry.register(
                        server_name=server_name,
                        tool_name=tool.name,
                        tool_schema=tool_dict
                    )
                    logger.debug(f"Registered tool '{tool.name}' from server '{server_name}'")

            # Log summary
            total_tools = len(self.registry)
            logger.info(
                f"MCP Client Manager initialized successfully with "
                f"{len(self.servers)} servers and {total_tools} tools"
            )

            # Log tool counts per server
            stats = self.registry.get_stats()
            for server_name, tool_count in stats["tools_per_server"].items():
                logger.info(f"  - {server_name}: {tool_count} tools")

        except Exception as e:
            logger.error(f"Failed to initialize MCP Client Manager: {e}", exc_info=True)
            raise RuntimeError(f"MCP initialization failed: {e}") from e

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool and return the result as a JSON string.

        This method:
        1. Looks up which server provides the requested tool
        2. Validates the tool exists
        3. Routes the call to the appropriate server
        4. Returns the result as a JSON-serialized string
        5. Catches and formats any errors as JSON

        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments to pass to the tool

        Returns:
            JSON string containing either:
            - The tool's result (on success)
            - An error object with error details (on failure)

        Examples:
            >>> await manager.call_tool("get_application", {"application_id": "123"})
            '{"id": "123", "student_name": "John Doe", ...}'

            >>> await manager.call_tool("invalid_tool", {})
            '{"error": "Tool not found", "tool_name": "invalid_tool"}'
        """
        logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")

        try:
            # Validate arguments is a dictionary
            if not isinstance(arguments, dict):
                raise ValueError(
                    f"Tool arguments must be a dictionary, got {type(arguments).__name__}"
                )

            # Lookup which server provides this tool
            server_name = self.registry.get_server_for_tool(tool_name)

            if not server_name:
                available_tools = self.registry.list_tool_names()
                error_result = {
                    "error": "Tool not found",
                    "tool_name": tool_name,
                    "available_tools": available_tools
                }
                logger.warning(f"Tool '{tool_name}' not found in registry")
                return json.dumps(error_result, indent=2)

            # Get the server instance
            server = self.servers.get(server_name)
            if not server:
                error_result = {
                    "error": "Server not found",
                    "tool_name": tool_name,
                    "server_name": server_name
                }
                logger.error(f"Server '{server_name}' not found for tool '{tool_name}'")
                return json.dumps(error_result, indent=2)

            # Call the tool on the server
            logger.debug(f"Routing tool '{tool_name}' to server '{server_name}'")
            result = await server.handle_tool_call(tool_name, arguments)

            # Serialize result to JSON
            result_json = json.dumps(result, indent=2, default=str)
            logger.info(f"Tool '{tool_name}' executed successfully")
            logger.debug(f"Tool result: {result_json}")

            return result_json

        except json.JSONDecodeError as e:
            # Handle JSON serialization errors
            error_result = {
                "error": "JSON serialization error",
                "tool_name": tool_name,
                "details": str(e)
            }
            logger.error(f"JSON serialization error for tool '{tool_name}': {e}")
            return json.dumps(error_result, indent=2)

        except ValueError as e:
            # Handle validation errors
            error_result = {
                "error": "Validation error",
                "tool_name": tool_name,
                "details": str(e)
            }
            logger.error(f"Validation error for tool '{tool_name}': {e}")
            return json.dumps(error_result, indent=2)

        except RuntimeError as e:
            # Handle tool execution errors
            error_result = {
                "error": "Tool execution error",
                "tool_name": tool_name,
                "details": str(e)
            }
            logger.error(f"Tool execution error for '{tool_name}': {e}")
            return json.dumps(error_result, indent=2)

        except Exception as e:
            # Handle unexpected errors
            error_result = {
                "error": "Unexpected error",
                "tool_name": tool_name,
                "error_type": type(e).__name__,
                "details": str(e)
            }
            logger.error(
                f"Unexpected error executing tool '{tool_name}': {e}",
                exc_info=True
            )
            return json.dumps(error_result, indent=2)

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools in Claude API format.

        Returns a list of tool schemas formatted for the Claude API's tools
        parameter. This allows Claude to know what tools are available and
        how to use them.

        The returned format matches Claude's expected tool schema:
        {
            "name": "tool_name",
            "description": "What the tool does",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }

        Returns:
            List of tool schema dictionaries in Claude API format

        Example:
            >>> tools = manager.get_available_tools()
            >>> len(tools)
            10
            >>> tools[0]["name"]
            'get_application'
        """
        logger.debug("Getting all available tools")

        all_tools = self.registry.get_all_tools()
        tool_list = []

        for tool_name, tool_schema in all_tools.items():
            # Convert from MCP format to Claude API format
            # MCP uses 'inputSchema', Claude expects 'input_schema'
            claude_format = {
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "input_schema": tool_schema["inputSchema"]
            }
            tool_list.append(claude_format)

        logger.info(f"Returning {len(tool_list)} available tools")
        return tool_list

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool schema by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Tool schema dictionary if found, None otherwise

        Example:
            >>> tool = manager.get_tool("get_application")
            >>> tool["description"]
            'Retrieve detailed information about a specific application'
        """
        logger.debug(f"Getting tool schema for '{tool_name}'")

        result = self.registry.lookup(tool_name)
        if result:
            server_name, tool_schema = result
            logger.debug(f"Found tool '{tool_name}' from server '{server_name}'")
            return tool_schema
        else:
            logger.debug(f"Tool '{tool_name}' not found")
            return None

    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """Get a server instance by name.

        This method provides direct access to server instances for cases
        where you need to call server methods directly rather than through
        the tool interface.

        Args:
            server_name: Name of the server to retrieve
                (application_data, analysis, context, or processor)

        Returns:
            MCPServer instance if found, None otherwise

        Example:
            >>> server = manager.get_server("application_data")
            >>> server.name
            'application_data'
        """
        logger.debug(f"Getting server '{server_name}'")

        server = self.servers.get(server_name)
        if server:
            logger.debug(f"Found server '{server_name}'")
        else:
            logger.debug(f"Server '{server_name}' not found")

        return server

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the MCP client manager.

        Returns:
            Dictionary containing:
            - total_servers: Number of registered servers
            - total_tools: Total number of tools
            - servers: List of server names
            - tools_per_server: Tool counts by server
            - registry_stats: Detailed registry statistics

        Example:
            >>> stats = manager.get_stats()
            >>> stats["total_tools"]
            10
            >>> stats["servers"]
            ['application_data', 'analysis', 'context', 'processor']
        """
        registry_stats = self.registry.get_stats()

        stats = {
            "total_servers": len(self.servers),
            "total_tools": len(self.registry),
            "servers": list(self.servers.keys()),
            "tools_per_server": registry_stats["tools_per_server"],
            "registry_stats": registry_stats
        }

        return stats

    def __repr__(self) -> str:
        """String representation of the manager.

        Returns:
            String describing the manager state
        """
        return (
            f"MCPClientManager(servers={len(self.servers)}, "
            f"tools={len(self.registry)})"
        )
