# Scholarship Copilot - Web Application

A web-based AI copilot assistant for analyzing scholarship applications using the Model Context Protocol (MCP) and Claude API.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Frontend (React/Vanilla JS)     │
│  - Chat interface                       │
│  - Application context sidebar          │
│  - Real-time updates                    │
└────────────┬────────────────────────────┘
             │ HTTP/REST API
┌────────────▼────────────────────────────┐
│      FastAPI Backend (Python)           │
│  - REST endpoints                       │
│  - Session management                   │
│  - MCP client manager                   │
└────────────┬────────────────────────────┘
             │ MCP Protocol
┌────────────▼────────────────────────────┐
│   MCP Servers (4 specialized servers)   │
│  - ApplicationDataMCPServer             │
│  - AnalysisMCPServer                    │
│  - ContextMCPServer                     │
│  - ProcessorMCPServer                   │
└────────────┬────────────────────────────┘
             │ Tool Calls
┌────────────▼────────────────────────────┐
│    Claude API (claude-opus-4-1)         │
│  - Intent classification                │
│  - Tool selection                       │
│  - Response generation                  │
└─────────────────────────────────────────┘
```

## Directory Structure

```
web/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app setup
│   │   ├── config.py               # Configuration
│   │   ├── api/
│   │   │   ├── routes.py           # REST endpoints
│   │   │   └── websocket.py        # WebSocket (future)
│   │   ├── mcp/
│   │   │   ├── client.py           # MCP client manager
│   │   │   ├── servers/
│   │   │   │   ├── base.py         # Base MCP server
│   │   │   │   ├── application_data.py
│   │   │   │   ├── analysis.py
│   │   │   │   ├── context.py
│   │   │   │   └── processor.py
│   │   │   └── tools/
│   │   │       ├── registry.py     # Tool registry
│   │   │       └── schemas.py      # Tool schemas
│   │   ├── copilot/
│   │   │   ├── agent.py            # Copilot agent
│   │   │   ├── intent.py           # Intent classification
│   │   │   └── prompts.py          # System prompts
│   │   ├── services/
│   │   │   ├── claude_client.py    # Claude API client
│   │   │   ├── session_manager.py  # Session management
│   │   │   └── data_access.py      # Data access layer
│   │   └── models/
│   │       └── schemas.py          # Pydantic models
│   ├── requirements.txt
│   └── run.py                      # Entry point
│
└── frontend/
    ├── index.html                  # Main HTML
    ├── app.js                      # Application logic
    ├── style.css                   # Styling
    └── README.md                   # Frontend docs
```

## Prerequisites

- Python 3.13+
- Node.js 18+ (optional, for frontend build tools)
- Claude API key (from Anthropic)
- Scholarship processor output (from main pipeline)

## Setup Instructions

### 1. Backend Setup

```bash
cd web/backend

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file in `web/backend/`:

```env
# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
ENVIRONMENT=development

# Claude API
ANTHROPIC_API_KEY=sk-ant-...  # Your API key here
CLAUDE_MODEL=claude-opus-4-1
CLAUDE_MAX_TOKENS=2048

# Paths (update as needed)
PROCESSOR_OUTPUT_PATH=../../output
APPLICATION_DATA_PATH=../../data

# Session
SESSION_TIMEOUT=3600
MAX_HISTORY=100

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Run Backend

```bash
# Option 1: Development with auto-reload
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Production
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Option 3: Using run.py
python3 run.py
```

Server will be available at: **http://localhost:8000**
- API: `http://localhost:8000/api/v1`
- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4. Frontend Setup

```bash
cd web/frontend

# Simple HTTP server (Python 3)
python3 -m http.server 3000

# Or using Node.js
npx http-server -p 3000

# Or using any other static server
```

Frontend will be available at: **http://localhost:3000**

## API Endpoints

### Session Management

```
POST /api/v1/sessions
  Create new session
  Request: {user_id: string}
  Response: {session_id, created_at, expires_at}

GET /api/v1/sessions/{session_id}
  Get session details
  Response: {session_id, context, history, ...}

PUT /api/v1/sessions/{session_id}
  Update session context
  Request: {session_id, context}
  Response: {updated: true}

DELETE /api/v1/sessions/{session_id}
  Delete session
  Response: {deleted: true}
```

### Chat

```
POST /api/v1/chat
  Send query to copilot
  Request: {query: string, session_id: string}
  Response: {response: string, session_id, timestamp}
```

### Tools

```
GET /api/v1/tools
  Get available MCP tools
  Response: {tools: [{name, description, inputSchema, ...}]}
```

### Health

```
GET /health
  Health check
  Response: {status, mcp_ready, claude_ready, session_count}
```

## Usage Examples

### 1. Create Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123"}'

# Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-11-15T18:00:00Z",
  "expires_at": "2024-11-15T19:00:00Z"
}
```

### 2. Send Query

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the strengths of this application?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# Response:
{
  "response": "Based on the analysis, the application shows strong academic achievement with a 3.9 GPA...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-11-15T18:05:00Z"
}
```

### 3. Get Tools

```bash
curl http://localhost:8000/api/v1/tools

# Response:
{
  "tools": [
    {
      "name": "get_application",
      "description": "Get application by ID",
      "inputSchema": {...}
    },
    ...
  ]
}
```

## Features

✅ **Multi-MCP Server Architecture**
- ApplicationDataMCPServer - Query applications
- AnalysisMCPServer - Analyze and compare
- ContextMCPServer - Manage sessions
- ProcessorMCPServer - Processor integration

✅ **Claude-Powered Intelligence**
- Intent classification
- Tool selection and execution
- Natural language analysis
- Multi-turn conversations

✅ **Session Management**
- User sessions with expiration
- Conversation history
- Application focus context
- Custom context data

✅ **REST API**
- Clean API design
- Proper HTTP status codes
- Error handling
- OpenAPI documentation

✅ **Frontend**
- Chat interface
- Application context sidebar
- Real-time updates
- Responsive design

## Development

### Adding New Tools

1. Define tool schema in `app/mcp/tools/schemas.py`
2. Add to appropriate MCP server
3. Implement handler function
4. Tool automatically registered and available to Claude

### Adding New MCP Servers

1. Create server class in `app/mcp/servers/`
2. Inherit from `MCPServer`
3. Implement `initialize()` and `handle_tool_call()`
4. Register in `MCPClientManager.initialize()`

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Get tools
curl http://localhost:8000/api/v1/tools

# OpenAPI docs
open http://localhost:8000/docs
```

## Troubleshooting

### "API key invalid"
- Check `ANTHROPIC_API_KEY` in `.env`
- Ensure key has access to Claude API

### "No processor output found"
- Verify `PROCESSOR_OUTPUT_PATH` points to correct directory
- Run scholarship processor first: `python process_scholarships.py`

### "MCP Server not responding"
- Check if path to processor output exists
- Verify file permissions
- Check server logs for errors

### CORS issues
- Ensure frontend URL is in `ALLOWED_ORIGINS` in `.env`
- Restart backend after changing CORS settings

## Performance Optimization

1. **Caching**
   - Tool schemas cached in memory
   - Application data indexed for fast lookup

2. **Async/Await**
   - All I/O operations are async
   - Non-blocking request handling

3. **Session Expiration**
   - Automatic cleanup of expired sessions
   - Prevents memory leak

## Deployment

### Docker

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY web/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web/backend/app ./app
COPY processor ./processor

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Use production Claude model
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper CORS origins
- [ ] Use database for sessions (replace in-memory)
- [ ] Set up logging and monitoring
- [ ] Enable HTTPS
- [ ] Set up rate limiting
- [ ] Configure backup/recovery

## Next Steps

1. **WebSocket Support** - Real-time streaming responses
2. **Authentication** - User authentication and authorization
3. **Database** - Replace in-memory session storage
4. **Caching** - Redis for performance
5. **Analytics** - Track queries and usage
6. **Fine-tuning** - Custom Claude instructions per scholarship

## Support

For issues or questions:
1. Check logs: `tail -f app.log`
2. Review API docs: `http://localhost:8000/docs`
3. Check design docs: `code/docs/MCP_COPILOT_CLAUDE_DESIGN.md`
