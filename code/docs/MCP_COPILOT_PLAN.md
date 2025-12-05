# AI Copilot with Model Context Protocol (MCP)

A web-based AI copilot assistant using the Model Context Protocol (MCP) to standardize tool integration and enable multiple agents to work with shared resources.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Browser                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Chat Interface │ Application Context │ Data Viewer  │  │
│  └──────────────────┬───────────────────────────────────┘  │
└────────────────────┼──────────────────────────────────────┘
                     │ WebSocket + REST API
┌────────────────────▼──────────────────────────────────────┐
│           FastAPI Backend (Python)                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  API Routes │ WebSocket Handler │ Session Mgmt  │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │     MCP Client & Tool Router                    │   │
│  │  ├─ Tool Registry                              │   │
│  │  ├─ Tool Dispatcher                            │   │
│  │  └─ MCP Server Manager                         │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │     MCP Servers (Protocol Implementation)      │   │
│  │  ├─ Application Data MCP Server                │   │
│  │  ├─ Processor MCP Server                       │   │
│  │  ├─ Analysis MCP Server                        │   │
│  │  └─ Context MCP Server                         │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │     Copilot Agent (uses MCP clients)           │   │
│  │  ├─ Intent Classification                      │   │
│  │  ├─ Tool Selection                             │   │
│  │  ├─ Response Generation                        │   │
│  │  └─ Context Management                         │   │
│  └──────────────────┬───────────────────────────────┘   │
└────────────────────┼──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│  Local Services & Data                                    │
│  ├─ Ollama (LLM inference)                               │
│  ├─ Processor Output (JSON files)                        │
│  ├─ Application Database                                 │
│  └─ Context Storage                                      │
└──────────────────────────────────────────────────────────┘
```

## MCP Components Overview

### 1. MCP Client (FastAPI Backend)
- Connects to MCP servers
- Routes tool calls to appropriate servers
- Manages server lifecycle
- Handles tool schemas and validation

### 2. MCP Servers (Protocol Implementation)
Each server implements the MCP protocol and provides specific capabilities:

**ApplicationDataMCPServer**
- Tools for querying application data
- Access to application profiles and metadata
- Search and filtering capabilities

**ProcessorMCPServer**
- Tools for interacting with processor pipeline
- Run processing steps
- Access processor output

**AnalysisMCPServer**
- Tools for performing analysis
- Comparison and aggregation
- Summary generation

**ContextMCPServer**
- Tools for managing session context
- Store and retrieve conversation history
- Application focus management

### 3. Tool Registry
Centralized registry of all available tools across MCP servers

## File Structure

```
web/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app setup
│   │   ├── config.py                  # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py              # REST endpoints
│   │   │   └── websocket.py           # WebSocket handler
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # MCP client manager
│   │   │   ├── servers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py            # Base MCP server class
│   │   │   │   ├── application_data.py
│   │   │   │   ├── processor.py
│   │   │   │   ├── analysis.py
│   │   │   │   └── context.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── registry.py        # Tool registry
│   │   │       ├── schemas.py         # Tool schemas
│   │   │       └── validators.py      # Input validation
│   │   ├── copilot/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # Main copilot agent
│   │   │   ├── intent.py              # Intent classification
│   │   │   └── prompts.py             # System prompts
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # Session management
│   │   │   ├── data_access.py         # Data access layer
│   │   │   └── ollama.py              # Ollama integration
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py             # Pydantic schemas
│   ├── requirements.txt
│   └── run.py                         # Entry point
└── frontend/
    ├── index.html
    ├── style.css
    ├── app.js
    └── ws-client.js
```

## MCP Implementation Details

### Base MCP Server Class

```python
# app/mcp/servers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class MCPServer(ABC):
    """Base class for MCP servers"""

    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, Dict[str, Any]] = {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the server"""
        pass

    @abstractmethod
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return result"""
        pass

    def register_tool(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a tool with its schema"""
        self.tools[name] = schema

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return all available tools"""
        return list(self.tools.values())
```

### Tool Schema Example

```python
# Tool schemas follow MCP standard format
{
    "name": "get_application",
    "description": "Retrieve application data by ID",
    "inputSchema": {
        "type": "object",
        "properties": {
            "app_id": {
                "type": "string",
                "description": "Application ID"
            }
        },
        "required": ["app_id"]
    }
}
```

### Application Data MCP Server

```python
# app/mcp/servers/application_data.py
class ApplicationDataMCPServer(MCPServer):
    """MCP server for application data operations"""

    async def initialize(self) -> None:
        self.register_tool("get_application", {
            "name": "get_application",
            "description": "Get application by ID",
            "inputSchema": {...}
        })
        self.register_tool("search_applications", {
            "name": "search_applications",
            "description": "Search applications by criteria",
            "inputSchema": {...}
        })
        # ... more tools

    async def handle_tool_call(self, tool_name: str, arguments: Dict) -> str:
        if tool_name == "get_application":
            return await self._get_application(arguments["app_id"])
        elif tool_name == "search_applications":
            return await self._search_applications(arguments)
        # ... more tools
```

### MCP Client Manager

```python
# app/mcp/client.py
class MCPClientManager:
    """Manages MCP servers and tool calls"""

    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.tool_registry: ToolRegistry = ToolRegistry()

    async def initialize(self) -> None:
        """Initialize all MCP servers"""
        servers = [
            ApplicationDataMCPServer("application_data"),
            ProcessorMCPServer("processor"),
            AnalysisMCPServer("analysis"),
            ContextMCPServer("context")
        ]

        for server in servers:
            await server.initialize()
            self.servers[server.name] = server
            # Register tools from server
            for tool in server.get_tools():
                self.tool_registry.register(server.name, tool)

    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """Call a tool through MCP"""
        server_name, tool = self.tool_registry.lookup(tool_name)
        server = self.servers[server_name]
        return await server.handle_tool_call(tool_name, arguments)

    def get_available_tools(self) -> List[Dict]:
        """Get all available tools"""
        return self.tool_registry.get_all_tools()
```

### Tool Registry

```python
# app/mcp/tools/registry.py
class ToolRegistry:
    """Registry of all available tools across servers"""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}  # name -> schema
        self.server_map: Dict[str, str] = {}  # tool_name -> server_name

    def register(self, server_name: str, tool_schema: Dict) -> None:
        """Register a tool from an MCP server"""
        tool_name = tool_schema["name"]
        self.tools[tool_name] = tool_schema
        self.server_map[tool_name] = server_name

    def lookup(self, tool_name: str) -> Tuple[str, Dict]:
        """Look up tool and its server"""
        server = self.server_map[tool_name]
        schema = self.tools[tool_name]
        return server, schema

    def get_all_tools(self) -> List[Dict]:
        """Get all registered tools"""
        return list(self.tools.values())
```

### Copilot Agent Using MCP

```python
# app/copilot/agent.py
class CopilotAgent:
    """Main copilot agent that uses MCP tools"""

    def __init__(self, mcp_client: MCPClientManager, ollama_client):
        self.mcp_client = mcp_client
        self.ollama = ollama_client
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager()

    async def process_query(self, query: str, session_id: str) -> str:
        # Load session context
        context = await self.context_manager.load(session_id)

        # Get available tools
        tools = self.mcp_client.get_available_tools()

        # Create system prompt with tools
        system_prompt = self._build_system_prompt(tools, context)

        # Call Ollama with tool info
        response = await self.ollama.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            tools=tools
        )

        # Handle tool calls if needed
        while response.get("tool_calls"):
            tool_calls = response["tool_calls"]
            results = []

            for call in tool_calls:
                result = await self.mcp_client.call_tool(
                    call["name"],
                    call["arguments"]
                )
                results.append({
                    "tool_name": call["name"],
                    "result": result
                })

            # Continue conversation with tool results
            response = await self.ollama.chat(
                messages=[...],
                tool_results=results
            )

        # Save to context
        await self.context_manager.save(session_id, context)

        return response.get("content", "")
```

## API Endpoints

### REST API

```
POST /api/v1/chat
  - Request: { query: string, session_id: string }
  - Response: { response: string, session_id: string }

GET /api/v1/tools
  - Response: { tools: [] }

GET /api/v1/session/{session_id}
  - Response: { context: object, history: [] }

POST /api/v1/session
  - Request: { user_id: string }
  - Response: { session_id: string }

WebSocket /ws/chat
  - Bidirectional real-time communication
```

## Data Flow: Query Processing

```
User Query
    ↓
[FastAPI Endpoint] → Validate input
    ↓
[Session Manager] → Load/create session
    ↓
[MCP Client] → Get available tools
    ↓
[System Prompt] → Build prompt with tool schemas
    ↓
[Ollama] → Call with query + tools
    ↓
[Tool Dispatcher] → Ollama selects tools
    ↓
[MCP Servers] → Execute selected tools
    ↓
[Tool Results] → Return to Ollama
    ↓
[Ollama] → Generate final response
    ↓
[Context Manager] → Save to session
    ↓
[Response] → Return to user
```

## Development Phases

### Phase 1: MCP Infrastructure (Week 1)
1. Set up FastAPI project
2. Create base MCP server class
3. Implement tool registry
4. Create MCP client manager
5. Set up configuration

### Phase 2: MCP Servers (Week 2)
1. Build ApplicationDataMCPServer
2. Build ProcessorMCPServer
3. Build AnalysisMCPServer
4. Build ContextMCPServer
5. Register all tools

### Phase 3: Copilot Agent (Week 3)
1. Implement CopilotAgent
2. Integrate with Ollama
3. Implement intent classification
4. Add context management
5. Add error handling

### Phase 4: API & WebSocket (Week 4)
1. Create REST endpoints
2. Implement WebSocket handler
3. Add session management
4. Add authentication (optional)
5. Error handling

### Phase 5: Frontend (Week 5)
1. Build chat interface HTML
2. Implement WebSocket client
3. Add message display
4. Add input handling
5. Add styling

### Phase 6: Integration & Testing (Week 6)
1. End-to-end testing
2. Performance optimization
3. Error handling
4. Documentation
5. Deployment

## Key Features

### Standardized Tool Interface
- All tools follow MCP schema
- Consistent validation
- Easy to add new tools

### Dynamic Tool Discovery
- Tools registered at runtime
- Ollama receives current tool list
- Tools can be enabled/disabled dynamically

### Proper Error Handling
- Tool execution errors caught
- Graceful fallback behavior
- Error messages to user

### Session Management
- Persistent session context
- Conversation history
- Application focus tracking

### Real-time Communication
- WebSocket for real-time updates
- Streaming responses (if supported)
- Live tool execution feedback

## Dependencies

```
fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.0.0
python-socketio>=5.10.0
python-engineio>=4.8.0
aiofiles>=23.2.0
python-dotenv>=1.0.0
httpx>=0.25.0
ollama>=0.1.0
```

## Environment Variables

```
# Server
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
ENVIRONMENT=development

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Paths
PROCESSOR_OUTPUT_PATH=./output
APPLICATION_DATA_PATH=./data

# Session
SESSION_TIMEOUT=3600
MAX_HISTORY=100

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://myserver.com
```

## Testing Strategy

1. **Unit Tests**: Test individual MCP servers
2. **Integration Tests**: Test tool calls end-to-end
3. **Agent Tests**: Test agent with mock Ollama
4. **API Tests**: Test REST and WebSocket endpoints
5. **Load Tests**: Performance testing

## Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY web/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web/backend/app ./app
COPY processor ./processor

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Advantages of Full MCP

✓ Standardized tool interface
✓ Easy to add new capabilities
✓ Multiple agents can share tools
✓ Tool discovery and validation
✓ Proper separation of concerns
✓ Production-ready architecture
✓ Future-proof design
✓ Easy to test and maintain
✓ Compatible with Claude and other models
