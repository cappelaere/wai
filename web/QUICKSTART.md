# Scholarship Copilot - Quick Start Guide

This guide will get you up and running with the Scholarship Copilot in minutes.

## Prerequisites

- Python 3.13+
- Anthropic API key (get from https://console.anthropic.com)
- Processed scholarship data (from running `process_scholarships.py`)

## 5-Minute Setup

### 1. Set up Backend Environment

```bash
cd web/backend

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create `web/backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
ENVIRONMENT=development
CLAUDE_MODEL=claude-opus-4-1
PROCESSOR_OUTPUT_PATH=../../output
```

### 3. Run Backend

```bash
python run.py
```

You should see:
```
Starting Scholarship Copilot in development mode
Server: 0.0.0.0:8000
Claude Model: claude-opus-4-1
```

**Backend is running at: http://localhost:8000**
- API: http://localhost:8000/api/v1
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Run Frontend (in new terminal)

```bash
cd web/frontend
python3 -m http.server 3000
```

**Frontend is running at: http://localhost:3000**

## First Steps

### 1. Test Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "mcp_ready": true,
  "claude_ready": true,
  "session_count": 0
}
```

### 2. View API Documentation

Open http://localhost:8000/docs in your browser to explore all API endpoints.

### 3. Open Chat Interface

Open http://localhost:3000 in your browser. You should see:
- Chat message area
- Input field for queries
- Application context sidebar
- Available tools list

### 4. Try a Query

In the chat interface, try:
```
"Show me all applications"
```

The copilot will:
1. Create a session
2. Call the appropriate MCP tools
3. Claude processes the tools and generates a response
4. Response appears in chat

## Architecture Overview

```
┌─────────────────────────┐
│   Browser (Frontend)    │
│  - Chat interface       │
│  - Real-time updates    │
└────────────┬────────────┘
             │ HTTP/REST
┌────────────▼────────────────┐
│  FastAPI Backend (Python)   │
│  - Session management       │
│  - MCP orchestration        │
│  - Claude integration       │
└────────────┬────────────────┘
             │ MCP Protocol
┌────────────▼────────────────┐
│  4 MCP Servers              │
│  - ApplicationData          │
│  - Analysis                 │
│  - Context                  │
│  - Processor                │
└────────────┬────────────────┘
             │ Tool calls
┌────────────▼────────────────┐
│  Claude API (claude-opus)   │
│  - Agentic loop             │
│  - Tool execution           │
│  - Response generation      │
└─────────────────────────────┘
```

## Understanding the System

### MCP Servers

1. **ApplicationDataMCPServer**
   - Loads scholarship applications from `output/` directory
   - Provides: `get_application()`, `search_applications()`, `list_applications()`

2. **AnalysisMCPServer**
   - Analyzes and compares applications
   - Provides: `analyze_application()`, `compare_applications()`, `generate_report()`

3. **ContextMCPServer**
   - Manages session state and current application focus
   - Provides: `get_context()`, `update_context()`, `set_current_application()`

4. **ProcessorMCPServer**
   - Verifies processor status and data availability
   - Provides: `get_processor_status()`, `verify_application_processed()`

### Session Management

- Each user gets a unique session ID
- Sessions track conversation history and context
- Automatic expiration after timeout (default 1 hour)
- In-memory storage (upgradable to database)

### Claude Integration

- Uses Claude Opus 4.1 model for superior reasoning
- Implements agentic loop: Query → Tool calls → Process results → Generate response
- Automatically selects appropriate MCP tools based on user intent
- Maintains conversation context across multiple turns

## Common Queries to Try

```
"What are all the scholarship applications we have?"

"Tell me about application ID app_123"

"Compare applications app_123 and app_456"

"What are the top strengths in the current application?"

"Generate a full analysis report for app_123"

"Show me statistics about all applications"
```

## Troubleshooting

### "API key invalid"
- Check `.env` file has correct `ANTHROPIC_API_KEY`
- Verify key at https://console.anthropic.com

### "No processor output found"
- Run `python process_scholarships.py` first to generate data
- Verify `output/` directory exists with JSON files

### "MCP Server not responding"
- Check backend console for error messages
- Verify all servers initialized: `http://localhost:8000/health`

### CORS Error in Browser Console
- Ensure frontend and backend URLs match CORS configuration
- Default: `http://localhost:3000` and `http://localhost:8000`

### Backend won't start
- Verify Python 3.13+ installed: `python3 --version`
- Verify venv activated: you should see `(venv)` in terminal
- Check dependencies installed: `pip list`

## Next Steps

1. **Test with Real Data**
   - Process scholarship data: `python process_scholarships.py`
   - Open chat interface and query applications

2. **Explore API Endpoints**
   - Visit http://localhost:8000/docs for interactive API explorer
   - Try endpoints with curl or Postman

3. **Customize**
   - Modify system prompts in `app/copilot/agent.py`
   - Add new MCP tools in `app/mcp/servers/`
   - Extend frontend with new UI features

4. **Production Deployment**
   - See ARCHITECTURE.md for deployment diagrams
   - See README.md for production checklist
   - Configure database, authentication, monitoring

## Files Structure

```
web/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI setup
│   │   ├── config.py         # Configuration
│   │   ├── mcp/              # MCP servers and tools
│   │   ├── copilot/          # Claude integration
│   │   ├── services/         # Session, Claude client
│   │   ├── api/              # REST endpoints
│   │   └── models/           # Pydantic schemas
│   ├── requirements.txt
│   ├── run.py
│   └── README.md
│
└── frontend/
    ├── index.html            # Chat interface
    ├── app.js                # Frontend logic
    ├── style.css             # Styling
    └── README.md
```

## Support

- **API Documentation**: http://localhost:8000/docs
- **Architecture Details**: Read `ARCHITECTURE.md`
- **Implementation Details**: Read `IMPLEMENTATION_SUMMARY.md`
- **Full Setup Guide**: Read `README.md`

## Quick Validation

After starting both backend and frontend, run these commands to verify:

```bash
# Check backend health
curl http://localhost:8000/health

# Check tools are loaded
curl http://localhost:8000/api/v1/tools | python3 -m json.tool

# Check frontend is accessible
curl http://localhost:3000
```

All should return 200 status codes and valid JSON.

Happy analyzing! 🎓
