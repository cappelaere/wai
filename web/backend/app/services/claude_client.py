"""
Claude API Client for handling AI interactions and tool calls.

This module provides a client for interacting with the Claude API,
including support for tool use and multi-turn conversations.
"""

import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Client for interacting with the Claude API.

    Handles message creation, tool calling, and multi-turn conversations
    with proper error handling and logging.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096
    ):
        """
        Initialize the Claude API client.

        Args:
            api_key: Anthropic API key. If not provided, uses settings.ANTHROPIC_API_KEY
            model: Claude model to use for API calls
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=self.api_key)

        logger.info(f"Initialized ClaudeClient with model: {self.model}")

    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat request to Claude with tool support.

        Args:
            messages: List of message objects with 'role' and 'content'
            tools: List of tool schemas in Anthropic format
            system: Optional system prompt

        Returns:
            Raw response object from Claude API

        Raises:
            APIError: If the API request fails
            APIConnectionError: If connection to API fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            logger.debug(f"Sending request to Claude API with {len(messages)} messages and {len(tools)} tools")
            logger.debug(f"Messages: {messages}")
            logger.debug(f"Tools: {tools}")

            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }

            # Add tools if provided
            if tools:
                api_params["tools"] = tools

            # Add system prompt if provided
            if system:
                api_params["system"] = system

            # Call Claude API
            response = self.client.messages.create(**api_params)

            logger.debug(f"Received response from Claude API: {response}")
            logger.info(f"API call successful. Stop reason: {response.stop_reason}")

            return response

        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIConnectionError as e:
            logger.error(f"Connection error to Claude API: {e}")
            raise
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat_with_tools: {e}")
            raise

    async def process_tool_calls(
        self,
        response: Any,
        mcp_client: Any,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_iterations: int = 10
    ) -> str:
        """
        Process tool calls from Claude's response and continue conversation.

        This method handles the agentic loop:
        1. Check if response contains tool_use blocks
        2. Execute each tool via MCP client
        3. Add results back to messages
        4. Call Claude again with results
        5. Repeat until Claude returns final text response

        Args:
            response: Initial response from Claude API
            mcp_client: MCP client for executing tools
            messages: Conversation messages list (will be modified in place)
            system: System prompt to use for subsequent calls
            max_iterations: Maximum number of tool call iterations to prevent infinite loops

        Returns:
            Final text response from Claude

        Raises:
            RuntimeError: If max iterations exceeded or tool execution fails
        """
        iteration = 0
        current_response = response

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Processing tool calls iteration {iteration}/{max_iterations}")

            # Check if response has tool use blocks
            tool_use_blocks = [
                block for block in current_response.content
                if block.type == "tool_use"
            ]

            if not tool_use_blocks:
                # No more tool calls, extract final text response
                logger.info("No tool use blocks found, extracting final response")
                final_text = self._extract_text_from_response(current_response)
                return final_text

            logger.info(f"Found {len(tool_use_blocks)} tool call(s) to process")

            # Add assistant's response to messages
            messages.append({
                "role": "assistant",
                "content": current_response.content
            })

            # Process each tool call
            tool_results = []
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_input = tool_block.input
                tool_id = tool_block.id

                logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")

                try:
                    # Call the tool via MCP client
                    tool_result = await mcp_client.call_tool(tool_name, tool_input)
                    logger.debug(f"Tool {tool_name} returned: {tool_result}")

                    # Add successful result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": str(tool_result)
                    })

                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    # Add error result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": f"Error executing tool: {str(e)}",
                        "is_error": True
                    })

            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results
            })

            logger.debug(f"Tool results added to messages: {tool_results}")

            # Call Claude again with tool results
            try:
                current_response = await self.chat_with_tools(
                    messages=messages,
                    tools=await mcp_client.get_tools() if mcp_client else [],
                    system=system
                )
            except Exception as e:
                logger.error(f"Error calling Claude API after tool execution: {e}")
                raise RuntimeError(f"Failed to get response after tool execution: {e}")

        # Max iterations exceeded
        logger.error(f"Maximum tool call iterations ({max_iterations}) exceeded")
        raise RuntimeError(
            f"Maximum tool call iterations ({max_iterations}) exceeded. "
            "Possible infinite loop detected."
        )

    def _extract_text_from_response(self, response: Any) -> str:
        """
        Extract text content from Claude response.

        Args:
            response: Response object from Claude API

        Returns:
            Concatenated text from all text blocks in response
        """
        text_blocks = [
            block.text for block in response.content
            if block.type == "text"
        ]

        final_text = "\n".join(text_blocks)
        logger.debug(f"Extracted text from response: {final_text}")

        return final_text
