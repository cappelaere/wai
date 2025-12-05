# MCP Copilot with Claude - Detailed Design

## Overview

This document specifies the MCP Copilot architecture using **Claude (claude-opus-4-1)** as the main orchestrator model instead of Ollama.

## Key Change: Claude as Orchestrator

### Why Claude?
- **Native MCP Support**: Claude has built-in MCP support
- **Better Reasoning**: Superior at intent classification and analysis
- **Tool Selection**: Excellent at selecting appropriate tools
- **Speed**: Faster responses than local LLMs
- **Capability**: Better at nuanced scholarship application analysis

### Architecture Change

**Before (Ollama)**:
```
User Query → MCP Client → Tool Registry → Ollama (with tools) → Response
```

**After (Claude)**:
```
User Query → FastAPI → Claude Client → Claude (with MCP tools) → MCP Servers → Response
```

## Claude Integration Details

### Claude Client Setup

```python
# app/services/claude_client.py
from anthropic import Anthropic

class ClaudeClient:
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-opus-4-1"
        self.max_tokens = 2048

    async def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict]
    ) -> Dict:
        """
        Call Claude with MCP tools available

        Args:
            messages: Conversation messages
            tools: Tool definitions from MCP servers

        Returns:
            Claude response with tool calls or text
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            tools=tools,
            messages=messages
        )
        return response
```

### Tool Definition Format for Claude

Claude requires tools in a specific format compatible with its API:

```python
{
    "name": "get_application",
    "description": "Retrieve complete application data by ID",
    "input_schema": {
        "type": "object",
        "properties": {
            "app_id": {
                "type": "string",
                "description": "The application ID"
            }
        },
        "required": ["app_id"]
    }
}
```

### MCP Tools Adapter

Since Claude calls tools directly, the MCP Client must translate Claude's tool calls to MCP server calls:

```python
# app/mcp/client.py
class MCPClientManager:
    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        Called by Claude when it selects a tool
        Routes to appropriate MCP server
        """
        server_name, tool_schema = self.tool_registry.lookup(tool_name)
        server = self.servers[server_name]

        result = await server.handle_tool_call(tool_name, arguments)

        return json.dumps(result)
```

## Copilot Agent with Claude

### Main Copilot Agent Logic

```python
# app/copilot/agent.py
class CopilotAgent:
    def __init__(
        self,
        claude_client: ClaudeClient,
        mcp_client: MCPClientManager,
        context_manager: ContextManager
    ):
        self.claude = claude_client
        self.mcp = mcp_client
        self.context = context_manager

    async def process_query(
        self,
        query: str,
        session_id: str
    ) -> str:
        """
        Process user query using Claude with MCP tools

        Flow:
        1. Load session context
        2. Get available MCP tools
        3. Build system prompt
        4. Call Claude with tools
        5. Handle tool calls (loop until done)
        6. Return response
        """

        # 1. Load context
        session = await self.context.load(session_id)
        current_app = session.current_application

        # 2. Get tools
        tools = self.mcp.get_available_tools()

        # 3. Build messages
        messages = await self._build_messages(
            query,
            session,
            current_app
        )

        # 4. Call Claude
        response = await self.claude.chat_with_tools(
            messages=messages,
            tools=tools
        )

        # 5. Handle tool calls (agentic loop)
        while self._has_tool_calls(response):
            # Execute tool calls
            for tool_use in response.content:
                if tool_use.type == "tool_use":
                    result = await self.mcp.call_tool(
                        tool_use.name,
                        tool_use.input
                    )

                    # Add result to messages
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": result
                            }
                        ]
                    })

            # Continue conversation with Claude
            response = await self.claude.chat_with_tools(
                messages=messages,
                tools=tools
            )

        # 6. Extract and save response
        final_response = self._extract_text_response(response)

        # Update context
        await self.context.save(session_id, {
            "current_application": current_app,
            "last_query": query,
            "last_response": final_response
        })

        return final_response

    async def _build_messages(
        self,
        query: str,
        session: Dict,
        current_app: str
    ) -> List[Dict]:
        """Build messages with system prompt and context"""

        system_prompt = f"""You are a scholarly analysis assistant helping users evaluate scholarship applications.

Context:
- Current application: {current_app or "None selected"}
- Session: {session.session_id}

Your role:
1. Use available tools to gather data about applications
2. Provide insightful analysis based on application profiles
3. Compare applications when requested
4. Answer questions about scholarship data
5. Maintain professional tone
6. Be specific - reference actual data from profiles

Guidelines:
- Always fetch data before analyzing
- For comparisons, always reference the current application focus
- Acknowledge limitations in the data
- Provide actionable insights
"""

        return [
            {"role": "user", "content": system_prompt + "\n\n" + query}
        ]

    def _has_tool_calls(self, response) -> bool:
        """Check if response contains tool calls"""
        return any(
            block.type == "tool_use"
            for block in response.content
        )

    def _extract_text_response(self, response) -> str:
        """Extract text content from Claude response"""
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)
```

## Message Format for Claude+MCP

### Initial Request
```json
{
  "role": "user",
  "content": "What are the key strengths of this application?"
}
```

### Claude Response with Tool Call
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll analyze the application for you. Let me retrieve the application data first."
    },
    {
      "type": "tool_use",
      "id": "toolu_0123456789",
      "name": "get_application_profiles",
      "input": {
        "app_id": "app_5678"
      }
    }
  ]
}
```

### Tool Result Message
```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_0123456789",
      "content": "{\"application_profile\": {...}, \"personal_profile\": {...}, ...}"
    }
  ]
}
```

### Claude Final Response
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Based on the analysis, the key strengths are:\n1. Strong academic record (3.8 GPA)...\n2. Demonstrated leadership..."
    }
  ]
}
```

## Configuration for Claude

### Environment Variables

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-opus-4-1
CLAUDE_MAX_TOKENS=2048

# MCP Servers
OLLAMA_HOST=http://localhost:11434  # Still optional for comparison
OLLAMA_MODEL=llama3.2

# Application
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Session
SESSION_TIMEOUT=3600
MAX_HISTORY=100

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://myserver.com
```

### Initialization

```python
# app/main.py
from fastapi import FastAPI
from anthropic import Anthropic

async def startup_event():
    # Initialize Claude client
    app.state.claude_client = ClaudeClient(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Initialize MCP client
    app.state.mcp_client = MCPClientManager()
    await app.state.mcp_client.initialize()

    # Initialize copilot
    app.state.copilot = CopilotAgent(
        claude_client=app.state.claude_client,
        mcp_client=app.state.mcp_client,
        context_manager=ContextManager()
    )
```

## Cost Considerations

### Claude API Pricing (as of 2024)
- **Claude Opus 4.1**:
  - Input: $15 per 1M tokens
  - Output: $45 per 1M tokens
- **Claude Sonnet 4**:
  - Input: $3 per 1M tokens
  - Output: $15 per 1M tokens

### Optimization Strategies

1. **Use Claude Sonnet for simple queries**
   - Cheaper, still capable
   - Good for data retrieval

2. **Use Claude Opus for complex analysis**
   - When comparison or deep analysis needed
   - Better reasoning for nuanced decisions

3. **Implement query batching**
   - Combine multiple questions
   - Reduce API calls

4. **Cache common queries**
   - Store frequent analysis results
   - 5-minute cache for same application focus

5. **Hybrid approach**
   ```python
   # Route based on query complexity
   if query_complexity_score > 0.7:
       model = "claude-opus-4-1"
   else:
       model = "claude-sonnet-4"
   ```

## Comparison: Claude vs Ollama Orchestrator

| Aspect | Claude | Ollama |
|--------|--------|--------|
| Cost | ~$0.01-0.05 per query | Free |
| Speed | Fast (1-3s) | Slower (5-30s) |
| Quality | Excellent | Good |
| MCP Support | Native | Manual |
| Privacy | Cloud | Local |
| Setup | API key | Self-hosted |
| Reasoning | Superior | Good |
| Tool Selection | Excellent | Adequate |
| Availability | 99.9% | Local only |

## Error Handling with Claude

### Rate Limiting
```python
from anthropic import RateLimitError

try:
    response = await self.claude.chat_with_tools(messages, tools)
except RateLimitError:
    # Exponential backoff
    await asyncio.sleep(2 ** retry_count)
    return await self.process_query(query, session_id)
```

### Token Limits
```python
if len(messages) > estimated_token_count(8000):
    # Summarize old messages
    messages = await self._compress_messages(messages)
```

### API Errors
```python
from anthropic import APIError, APIConnectionError

try:
    response = await claude.chat_with_tools(...)
except APIConnectionError:
    return "Connection error. Please try again."
except APIError as e:
    logger.error(f"Claude API error: {e}")
    return "Service error. Please try again later."
```

## Dependencies Update

```
fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.0.0
anthropic>=0.25.0      # NEW: Claude API client
python-socketio>=5.10.0
python-engineio>=4.8.0
aiofiles>=23.2.0
python-dotenv>=1.0.0
httpx>=0.25.0
```

## Testing with Claude

### Mock Claude for Testing
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_copilot_with_mock_claude():
    mock_response = {
        "content": [
            {
                "type": "text",
                "text": "This is a test response"
            }
        ]
    }

    with patch.object(ClaudeClient, 'chat_with_tools', return_value=mock_response):
        agent = CopilotAgent(...)
        response = await agent.process_query("Test query", "session_123")
        assert response == "This is a test response"
```

## Deployment Notes

### Production Checklist
- [ ] Store ANTHROPIC_API_KEY in secure vault (not .env)
- [ ] Set up rate limiting on API endpoints
- [ ] Implement request logging
- [ ] Monitor Claude API usage and costs
- [ ] Set up alerts for quota limits
- [ ] Implement fallback behavior if Claude unavailable
- [ ] Use Claude Sonnet in production (better cost/benefit)

### Security
- Never log API keys
- Never expose API keys in frontend
- Validate all tool inputs before MCP call
- Rate limit per user
- Implement API key rotation

## Summary

Using Claude as the orchestrator provides:
- **Better analysis quality** through superior reasoning
- **Native MCP support** (designed together)
- **Faster response times** than local LLMs
- **Excellent tool selection** for complex queries
- **Professional-grade reliability**

The trade-off is **API costs**, but the improved user experience and reduced infrastructure overhead typically justify the cost for production systems.
