"""
Main Copilot Agent for scholarship application analysis.

This module provides the core agent logic for processing user queries,
managing tool calls, and coordinating between Claude AI and MCP tools.
"""

import logging
from typing import List, Dict, Any, Optional

from app.services.claude_client import ClaudeClient
from app.mcp.client import MCPClientManager
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class CopilotAgent:
    """
    Main copilot agent for processing scholarship analysis queries.

    Coordinates between Claude AI, MCP tools, and session management
    to provide intelligent analysis of scholarship applications.
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        mcp_client: MCPClientManager,
        context_manager: SessionManager
    ):
        """
        Initialize the copilot agent.

        Args:
            claude_client: Client for Claude AI interactions
            mcp_client: Manager for MCP tool connections
            context_manager: Manager for session context and history
        """
        self.claude_client = claude_client
        self.mcp_client = mcp_client
        self.context_manager = context_manager

        logger.info("Initialized CopilotAgent")

    async def process_query(
        self,
        query: str,
        session_id: str
    ) -> str:
        """
        Process a user query and return the agent's response.

        This is the main entry point for the copilot agent. It:
        1. Loads session context
        2. Gets available tools from MCP
        3. Builds messages with system prompt
        4. Calls Claude with tools
        5. Processes any tool calls
        6. Saves the interaction to session
        7. Returns final response

        Args:
            query: User's question or request
            session_id: Unique identifier for the conversation session

        Returns:
            Final text response from the agent

        Raises:
            Exception: If query processing fails
        """
        try:
            logger.info(f"Processing query for session {session_id}: {query[:100]}...")

            # Load session context
            session = await self.context_manager.get_session(session_id)
            logger.debug(f"Loaded session: {session}")

            # Get available tools from MCP
            tools = await self.mcp_client.get_tools()
            logger.info(f"Retrieved {len(tools)} tools from MCP")

            # Build system prompt
            current_app = session.get("current_application")
            system_prompt = self._build_system_prompt(tools, current_app)

            # Build messages list
            messages = await self._build_messages(query, session)

            # Call Claude with tools
            logger.info("Calling Claude API with tools")
            response = await self.claude_client.chat_with_tools(
                messages=messages,
                tools=tools,
                system=system_prompt
            )

            # Process tool calls (if any) and get final response
            logger.info("Processing tool calls")
            final_response = await self.claude_client.process_tool_calls(
                response=response,
                mcp_client=self.mcp_client,
                messages=messages,
                system=system_prompt
            )

            # Save query and response to session context
            await self.context_manager.add_interaction(
                session_id=session_id,
                query=query,
                response=final_response
            )

            logger.info(f"Successfully processed query for session {session_id}")
            return final_response

        except Exception as e:
            logger.error(f"Error processing query for session {session_id}: {e}", exc_info=True)
            raise

    def _build_system_prompt(
        self,
        tools: List[Dict[str, Any]],
        current_app: Optional[str] = None
    ) -> str:
        """
        Build the system prompt for Claude.

        Creates a comprehensive system prompt that includes:
        - Role description
        - Current context (focused application)
        - Available tools
        - Guidelines for analysis

        Args:
            tools: List of available tool schemas
            current_app: ID of currently focused application (if any)

        Returns:
            Complete system prompt string
        """
        # Build tools list for the prompt
        tools_list = "\n".join([
            f"- {tool['name']}: {tool.get('description', 'No description')}"
            for tool in tools
        ])

        # Create system prompt
        system_prompt = f"""You are a scholarly analysis assistant helping users evaluate scholarship applications.

Current Context:
- Application Focus: {current_app or "None selected"}

Your role:
1. Use available tools to gather application data
2. Provide insightful, specific analysis based on actual profiles
3. Compare applications when requested
4. Answer questions about scholarship data
5. Maintain professional tone

Available Tools:
{tools_list}

Guidelines:
- Always fetch data before analyzing
- Reference specific data from profiles
- For comparisons, reference the current application
- Acknowledge data limitations
- Provide actionable insights
- Be concise but thorough
- Use structured formatting (lists, sections) when helpful
- If you need to compare applications, ask which ones to compare
- When analyzing an application, consider: academic merit, research potential, personal statement quality, recommendations, and overall fit

Remember: Your analysis should be evidence-based and reference specific details from the application data."""

        logger.debug(f"Built system prompt with {len(tools)} tools")
        return system_prompt

    async def _build_messages(
        self,
        query: str,
        session: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build the messages list for Claude API.

        Constructs the conversation history from session context
        and adds the current user query.

        Args:
            query: Current user query
            session: Session object containing conversation history

        Returns:
            List of message objects in Claude API format
        """
        messages = []

        # Add conversation history from session
        history = session.get("history", [])
        for interaction in history:
            # Add user message
            messages.append({
                "role": "user",
                "content": interaction["query"]
            })
            # Add assistant response
            messages.append({
                "role": "assistant",
                "content": interaction["response"]
            })

        # Add current query
        messages.append({
            "role": "user",
            "content": query
        })

        logger.debug(f"Built messages list with {len(messages)} messages")
        return messages
