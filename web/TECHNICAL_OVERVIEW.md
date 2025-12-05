# Scholarship Copilot - Technical Overview

Comprehensive technical documentation for developers working with the Scholarship Copilot system.

## System Architecture

### High-Level Flow

```
User Query (Frontend)
    ↓
    │ HTTP POST /api/v1/chat
    ↓
Session Manager
    ├─ Load/Create session
    ├─ Track conversation history
    └─ Manage context
    ↓
Copilot Agent
    ├─ Build system prompt
    ├─ Add conversation history
    └─ Format for Claude API
    ↓
Claude API (claude-opus-4-1)
    ├─ Process with agentic loop
    ├─ Select appropriate tools
    └─ Return tool calls
    ↓
MCP Client Manager
    ├─ Route tool calls to servers
    └─ Process results
    ↓
MCP Servers (4 specialized servers)
    ├─ ApplicationDataMCPServer → Load application data
    ├─ AnalysisMCPServer → Analyze applications
    ├─ ContextMCPServer → Manage session context
    └─ ProcessorMCPServer → Check processor status
    ↓
Claude API (Process results)
    ├─ Generate natural language response
    └─ Continue agentic loop if needed
    ↓
Session Manager (Save response)
    └─ Add to conversation history
    ↓
API Response (Frontend)
```

## Component Deep Dive

### 1. FastAPI Application (`app/main.py`)

**Responsibility**: Initialize the FastAPI application and manage lifecycle

**Key Components**:
```python
# Startup event
@app.on_event("startup")
async def startup_event():
    - Initialize SessionManager (in-memory session storage)
    - Initialize MCPClientManager (all 4 MCP servers)
    - Initialize ClaudeClient
    - Initialize CopilotAgent
    - Run initial MCP server checks

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    - Cleanup sessions
    - Close external connections
    - Log statistics

# CORS Configuration
- Allows requests from ALLOWED_ORIGINS (configured in .env)
- Enables credentials for cross-origin requests
```

**Startup Order** (Critical):
1. SessionManager first (other components depend on it)
2. MCPClientManager (initializes all 4 MCP servers)
3. ClaudeClient (needs API key from config)
4. CopilotAgent (uses MCPClientManager and ClaudeClient)

### 2. Configuration (`app/config.py`)

**Responsibility**: Centralized configuration management

**Key Settings**:
```python
class Settings(BaseSettings):
    # Server
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    environment: str = "development"
    debug: bool = False

    # Claude API
    anthropic_api_key: str  # Required
    claude_model: str = "claude-opus-4-1"
    claude_max_tokens: int = 2048

    # Paths
    processor_output_path: Path = Path("../../output")
    application_data_path: Path = Path("../../data")

    # Session
    session_timeout: int = 3600  # seconds
    max_history: int = 100

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]
```

**Environment Variables**:
- All settings can be overridden via environment variables
- Prefix: `SCHOLARSHIP_` (optional for most)
- Load from `.env` file using `python-dotenv`

### 3. MCP Infrastructure

#### 3.1 Base MCP Server (`app/mcp/servers/base.py`)

**Responsibility**: Abstract base class for all MCP servers

**Key Methods**:
```python
class MCPServer:
    async def initialize(self):
        # Load tools and initialize server
        # Called during app startup

    async def handle_tool_call(self, tool_name: str, tool_input: Dict) -> Dict:
        # Execute tool and return result
        # Called by MCP client manager

    def register_tool(self, tool_name: str, schema: Dict, handler: Callable):
        # Register a tool with schema and handler

    def get_tools(self) -> List[Dict]:
        # Return all tools in Claude-format
```

**Attributes**:
- `name`: Server identifier (e.g., "application_data")
- `tools`: Dict mapping tool_name → (schema, handler)
- `client_context`: Shared context across servers

#### 3.2 Tool Registry (`app/mcp/tools/registry.py`)

**Responsibility**: Centralized tool management

**Key Methods**:
```python
class ToolRegistry:
    def register(self, tool_name: str, server_name: str, schema: Dict):
        # Register tool_name pointing to server_name

    def lookup(self, tool_name: str) -> Tuple[str, Dict]:
        # Get (server_name, schema) for tool

    def get_all_tools(self) -> List[Dict]:
        # Get all tools in Claude-format

    def get_tools_by_server(self, server_name: str) -> List[Dict]:
        # Get all tools for specific server
```

**Data Structure**:
```python
registry = {
    "get_application": {
        "server": "application_data",
        "schema": {...}
    },
    "analyze_application": {
        "server": "analysis",
        "schema": {...}
    },
    # ... more tools
}
```

#### 3.3 Tool Schemas (`app/mcp/tools/schemas.py`)

**Responsibility**: Define all tool schemas in Claude MCP format

**Format**: JSON Schema compatible with Claude API

**Tools Defined** (20+ total):

1. **ApplicationData Server**:
   - `get_application(application_id)` → Full application data
   - `search_applications(query)` → List of matching applications
   - `list_applications()` → All applications
   - `get_application_profiles(application_id)` → All 5 profiles

2. **Analysis Server**:
   - `analyze_application(application_id)` → Strengths/weaknesses
   - `compare_applications(app_ids)` → Comparison ranking
   - `generate_report(application_id)` → Full analysis report

3. **Context Server**:
   - `get_context(session_id)` → Current session context
   - `update_context(session_id, context)` → Update context
   - `get_current_application(session_id)` → Focused application
   - `set_current_application(session_id, app_id)` → Set focus

4. **Processor Server**:
   - `get_processor_status()` → Overall processor status
   - `verify_application_processed(application_id)` → Check if complete

### 4. MCP Servers

#### 4.1 ApplicationDataMCPServer

**Purpose**: Query and retrieve scholarship applications

**Data Source**: Reads from `output/{year}/{scholarship}/{app_id}/` directory

**Tool Implementations**:

```python
async def get_application(application_id: str):
    # Load all 5 profiles for an application
    # Returns: {application, personal, recommendation, academic, social}

async def search_applications(query: str):
    # Search applications by name/email/status
    # Returns: List of matching application IDs

async def list_applications():
    # Get all application IDs
    # Returns: List of all available applications
```

**Performance Optimization**:
- Lazy loading (only load requested applications)
- JSON caching for frequently accessed apps
- Directory structure indexed on startup

#### 4.2 AnalysisMCPServer

**Purpose**: Analyze and compare scholarship applications

**Analysis Algorithms**:

```python
async def analyze_application(application_id: str):
    # Analyze single application
    # Returns:
    # {
    #   "overall_score": 0-100,
    #   "category_scores": {...},
    #   "strengths": ["strength1", "strength2"],
    #   "weaknesses": ["weakness1", "weakness2"],
    #   "recommendation": "accept/review/decline"
    # }
```

**Scoring Logic**:
- Academic: GPA, test scores, achievements
- Personal: Writing quality, unique experiences
- Recommendation: Strength of letters, specificity
- Social: Community involvement, leadership

#### 4.3 ContextMCPServer

**Purpose**: Manage per-session state and context

**Data Storage**: In-memory dict (production: PostgreSQL)

**Context Structure**:
```python
session_context = {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "current_application": "app_123",
    "analysis_type": "full",
    "metadata": {
        "created_at": "2024-11-15T18:00:00Z",
        "last_query": "What are strengths?",
        "query_count": 5
    }
}
```

**Key Operations**:
- `get_context()` → Retrieve session context
- `update_context()` → Update specific fields
- `set_current_application()` → Focus on application
- `track_query()` → Log user query

#### 4.4 ProcessorMCPServer

**Purpose**: Verify processor status and data availability

**Tool Implementations**:

```python
async def get_processor_status():
    # Check overall processor state
    # Returns: {total_apps, processed, failed, pending}

async def verify_application_processed(application_id: str):
    # Check if specific app is fully processed
    # Returns: {complete: bool, missing_steps: [...]}
```

### 5. MCP Client Manager (`app/mcp/client.py`)

**Responsibility**: Orchestrate all MCP servers and route tool calls

**Initialization**:
```python
async def initialize(self):
    # 1. Initialize all 4 MCP servers in parallel
    # 2. Collect tools from each server
    # 3. Register all tools in ToolRegistry
    # 4. Cache tool schemas for Claude
```

**Tool Call Routing**:
```python
async def call_tool(tool_name: str, tool_input: Dict) -> Dict:
    # 1. Lookup server from registry
    # 2. Route to appropriate MCP server
    # 3. Execute tool handler
    # 4. Return result (or error)
```

**Tool Discovery**:
```python
def get_available_tools(self) -> List[Dict]:
    # Return all tools in Claude API format
    # Called by frontend /api/v1/tools endpoint
```

### 6. Claude Integration (`app/services/claude_client.py`)

**Responsibility**: Interact with Claude API with agentic loop

**Agentic Loop**:

```
1. User Query
    ↓
2. Call Claude with query + tools
    ↓
3. Claude returns:
    - Response text (if final answer)
    - Tool calls (if needs data)
    ↓
4. If tool calls:
    - Execute each tool via MCP
    - Collect results
    - Add to message history
    - Loop back to step 2
    ↓
5. If final response:
    - Extract text
    - Return to user
    - Done
```

**Implementation**:

```python
async def chat_with_tools(
    messages: List[Dict],
    tools: List[Dict],
    max_iterations: int = 10
) -> Dict:
    # Main agentic loop
    for iteration in range(max_iterations):
        # Call Claude
        response = await client.messages.create(
            model="claude-opus-4-1",
            max_tokens=2048,
            tools=tools,
            messages=messages
        )

        # Check for tool calls
        tool_calls = [block for block in response.content
                     if block.type == "tool_use"]

        if not tool_calls:
            # Final response
            return {"response": extract_text(response)}

        # Process tool calls
        for tool_call in tool_calls:
            result = await mcp.call_tool(
                tool_call.name,
                tool_call.input
            )
            # Add result to messages for Claude
```

**Error Handling**:
- RateLimitError: Automatic retry with exponential backoff
- APIConnectionError: Retry up to 3 times
- APIError: Log and return error message
- Max iterations exceeded: Return partial response

### 7. Copilot Agent (`app/copilot/agent.py`)

**Responsibility**: High-level orchestration of conversation

**Main Flow**:

```python
async def process_query(query: str, session_id: str) -> str:
    # 1. Load session (get conversation history)
    session = session_manager.load_session(session_id)

    # 2. Get available tools
    tools = mcp_client.get_available_tools()

    # 3. Build system prompt (context-aware)
    system_prompt = build_system_prompt(
        tools,
        current_application=session.context.current_application
    )

    # 4. Build message history
    messages = build_messages(query, session)

    # 5. Call Claude with agentic loop
    result = await claude_client.chat_with_tools(
        messages,
        tools
    )

    # 6. Save response to session history
    session_manager.add_message(
        session_id,
        "user",
        query
    )
    session_manager.add_message(
        session_id,
        "assistant",
        result["response"]
    )

    # 7. Return response
    return result["response"]
```

**System Prompt Design**:

```
You are an AI copilot for analyzing scholarship applications.

Current Focus Application: {current_application}

Available Tools:
{tool_descriptions}

Guidelines:
1. Use tools to gather data before analysis
2. Provide specific, actionable insights
3. Compare applications when requested
4. Always reference application IDs in responses
5. Suggest strengths and weaknesses based on data
```

### 8. Session Manager (`app/services/session_manager.py`)

**Responsibility**: Manage per-user sessions and conversation state

**Session Structure**:
```python
session = {
    "session_id": str,  # UUID
    "user_id": str,
    "created_at": datetime,
    "expires_at": datetime,
    "context": {
        "current_application": Optional[str],
        "analysis_type": str,
        "metadata": Dict
    },
    "messages": [
        {"role": "user", "content": str, "timestamp": datetime},
        {"role": "assistant", "content": str, "timestamp": datetime}
    ]
}
```

**Key Methods**:

```python
async def create_session(user_id: str) -> Dict:
    # Create new session with UUID
    # Set expiration to now + timeout

async def load_session(session_id: str) -> Dict:
    # Get session by ID
    # Check if expired (return None if so)

async def update_context(session_id: str, context: Dict):
    # Merge context update into session

async def add_message(
    session_id: str,
    role: str,
    content: str
):
    # Add message to conversation history
    # Truncate if exceeds max_history

async def cleanup_expired():
    # Remove expired sessions
    # Called periodically
```

**Session Expiration**:
- Timeout: 3600 seconds (1 hour) configurable
- Checked on access
- Auto-cleanup every 30 minutes

### 9. REST API Routes (`app/api/routes.py`)

**Responsibility**: Expose functionality via HTTP endpoints

**7 Core Endpoints**:

#### POST /api/v1/sessions
Create new user session
```
Request: {"user_id": "user_123"}
Response: {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-11-15T18:00:00Z",
    "expires_at": "2024-11-15T19:00:00Z"
}
```

#### POST /api/v1/chat
Send query to copilot
```
Request: {
    "query": "What are the strengths?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
Response: {
    "response": "Based on analysis...",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-11-15T18:05:00Z"
}
```

#### GET /api/v1/sessions/{session_id}
Get session details
```
Response: {
    "session_id": "...",
    "context": {...},
    "messages": [...],
    "expires_at": "..."
}
```

#### PUT /api/v1/sessions/{session_id}
Update session context
```
Request: {
    "context": {
        "current_application": "app_456",
        "analysis_type": "quick"
    }
}
Response: {"updated": true}
```

#### DELETE /api/v1/sessions/{session_id}
Delete session
```
Response: {"deleted": true}
```

#### GET /api/v1/tools
List available tools
```
Response: {
    "tools": [
        {
            "name": "get_application",
            "description": "...",
            "inputSchema": {...}
        }
    ]
}
```

#### GET /health
Health check
```
Response: {
    "status": "healthy",
    "mcp_ready": true,
    "claude_ready": true,
    "session_count": 5,
    "uptime_seconds": 3600
}
```

### 10. Data Models (`app/models/schemas.py`)

**Responsibility**: Pydantic validation models

**Key Models**:
```python
class SessionRequest(BaseModel):
    user_id: str

class ChatRequest(BaseModel):
    query: str
    session_id: str

class ContextRequest(BaseModel):
    context: Dict[str, Any]

class ToolSchema(BaseModel):
    name: str
    description: str
    inputSchema: Dict

class HealthResponse(BaseModel):
    status: str
    mcp_ready: bool
    claude_ready: bool
    session_count: int
```

## Frontend Architecture

### HTML Structure (`frontend/index.html`)

```html
<body>
  <div class="container">
    <!-- Header -->
    <header>
      <h1>Scholarship Copilot</h1>
      <div id="sessionId">Session: ...</div>
    </header>

    <!-- Main Content -->
    <div class="main-grid">
      <!-- Chat Area -->
      <div class="chat-container">
        <div id="chatMessages"></div>
        <form id="chatForm">
          <input id="queryInput" type="text" placeholder="Ask...">
          <button class="button-send">Send</button>
        </form>
      </div>

      <!-- Sidebar -->
      <aside class="sidebar">
        <div id="currentApp">Current Application</div>
        <div id="toolsList">Available Tools</div>
      </aside>
    </div>
  </div>
</body>
```

### JavaScript Flow (`frontend/app.js`)

```javascript
// 1. Page Load
DOMContentLoaded
  ├─ initializeSession()      // POST /api/v1/sessions
  ├─ setupEventListeners()    // Attach event handlers
  └─ loadTools()              // GET /api/v1/tools

// 2. User Input
handleQuerySubmit()
  ├─ Add message to UI
  ├─ POST /api/v1/chat        // Send query
  ├─ Receive response
  ├─ Add response to UI
  ├─ updateApplicationContext() // GET /api/v1/sessions/{id}
  └─ Clear input

// 3. UI Updates
addMessage(role, content)
  ├─ Create message element
  ├─ Set role-based styling
  └─ Scroll to bottom
```

## Data Flow Diagram

### Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User types: "What are the strengths of app_123?"                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: fetch POST /api/v1/chat                              │
│ {query: "...", session_id: "..."}                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend Route Handler                                           │
│ - Load session from SessionManager                              │
│ - Pass to CopilotAgent.process_query()                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ CopilotAgent                                                    │
│ - Build system prompt with context                             │
│ - Format conversation history                                  │
│ - Call ClaudeClient.chat_with_tools()                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ ClaudeClient (Agentic Loop - Iteration 1)                       │
│ Call: POST https://api.anthropic.com/messages                  │
│ With: messages + tools list                                     │
│                                                                 │
│ Claude returns: [ToolUseBlock("get_application", ...)]         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ ClaudeClient: Process Tool Calls                                │
│ For each tool call:                                             │
│ - Call MCPClientManager.call_tool(name, input)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ MCPClientManager                                                │
│ - Lookup tool in ToolRegistry                                  │
│ - Route to ApplicationDataMCPServer.get_application()           │
│ - Return application data                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ ClaudeClient (Agentic Loop - Iteration 2)                       │
│ Add tool result to messages                                     │
│ Call Claude again with enriched context                         │
│                                                                 │
│ Claude returns: [TextBlock("Based on the data... strengths")]  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ CopilotAgent                                                    │
│ - Extract response text                                         │
│ - Save to session history                                       │
│ - Return response                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend Route Handler                                           │
│ Return: HTTP 200 with response                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Frontend                                                        │
│ - Display response in chat                                      │
│ - Update application context sidebar                            │
│ - Ready for next query                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Latency (Typical)
- Session Creation: <100ms
- Tool Query (ApplicationData): <50ms
- Claude API Call: 1-3 seconds
- Total Response: 2-5 seconds

### Throughput
- Single server: ~5-10 concurrent users
- With load balancing: Scales horizontally

### Memory Usage
- Per session: ~10-20KB
- 1000 sessions: ~10-20MB
- With 100KB chat history: 1-2GB

## Security Considerations

### API Key Management
- ✅ Stored in environment variables only
- ✅ Never logged or exposed in responses
- ✅ Validated on startup

### Input Validation
- ✅ All inputs validated via Pydantic
- ✅ Query length limited
- ✅ Session ID validated as UUID

### CORS
- ✅ Configured for specific origins only
- ✅ Credentials properly handled
- ⚠️ Need: Rate limiting per origin

### Session Security
- ✅ UUID-based session IDs (cryptographically secure)
- ✅ Session expiration enforced
- ⚠️ TODO: User authentication layer

### Data Privacy
- ✅ Session data isolated per user
- ✅ Conversation history kept separate
- ⚠️ TODO: Encrypted session storage

## Testing Strategy

### Unit Tests Needed
- Tool schemas validation
- Session manager lifecycle
- MCP server initialization
- Claude client agentic loop

### Integration Tests Needed
- End-to-end API flow
- Frontend to backend communication
- MCP tool execution with real data
- Claude API integration (mocked)

### Manual Testing
- Follow QUICKSTART.md
- Test each API endpoint
- Verify frontend chat works
- Test with sample data

## Debugging Tips

### Enable Debug Logging
```python
# In app/config.py
LOG_LEVEL = "DEBUG"
```

### Check Session State
```bash
# In running app:
# Session manager logs all operations
journalctl -u scholarship-copilot | grep SESSION
```

### Monitor MCP Servers
```python
# Add debug logging in mcp/client.py
logger.debug(f"Calling tool: {tool_name} on server: {server_name}")
```

### Test Claude Integration
```bash
# Test API key is valid
curl https://api.anthropic.com/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY"
```

## Future Enhancements

### Short Term
- [ ] WebSocket support for real-time responses
- [ ] Database backend for session storage
- [ ] User authentication
- [ ] Rate limiting

### Medium Term
- [ ] Redis caching for tools
- [ ] File upload support
- [ ] PDF export functionality
- [ ] Analytics dashboard

### Long Term
- [ ] Fine-tuned Claude models
- [ ] Multi-organization support
- [ ] Workflow automation
- [ ] External system integration

---

**Document Version**: 1.0
**Last Updated**: November 2024
**Status**: Comprehensive - Ready for Development
