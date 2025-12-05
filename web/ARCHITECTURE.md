# Scholarship Copilot - Architecture Diagram

## System Architecture Overview

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                          USER'S BROWSER / FRONTEND                          ║
║                                                                             ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │                      Web Interface (HTML/CSS/JS)                     │  ║
║  │                                                                      │  ║
║  │  ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────┐   │  ║
║  │  │   Chat Interface    │  │ Application      │  │ Tools Panel  │   │  ║
║  │  │                     │  │ Context Sidebar  │  │              │   │  ║
║  │  │ • Message list      │  │                  │  │ • Available  │   │  ║
║  │  │ • Input form        │  │ • Current app    │  │   tools      │   │  ║
║  │  │ • Loading state     │  │ • Focus context  │  │ • Schemas    │   │  ║
║  │  └─────────────────────┘  └──────────────────┘  └──────────────┘   │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
│                                     │                                       │
│                          REST API (HTTP/JSON)                               │
│                                     │                                       │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
╔═════════════════════════════════════╧═════════════════════════════════════╗
║                         FASTAPI BACKEND SERVER                           ║
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐ ║
║  │                     API Routes & Request Handling                   │ ║
║  │                     (app/api/routes.py)                             │ ║
║  │                                                                     │ ║
║  │  POST /api/v1/sessions      → Create session                       │ ║
║  │  POST /api/v1/chat          → Process query                        │ ║
║  │  GET /api/v1/sessions/{id}  → Get session details                  │ ║
║  │  PUT /api/v1/sessions/{id}  → Update context                       │ ║
║  │  DELETE /api/v1/sessions/{id} → Delete session                     │ ║
║  │  GET /api/v1/tools          → List available tools                 │ ║
║  │  GET /health                → Health check                         │ ║
║  └──────────────────────────┬──────────────────────────────────────────┘ ║
║                             │                                            ║
║  ┌──────────────────────────▼──────────────────────────────────────────┐ ║
║  │                 Core Services & Managers                            │ ║
║  │                                                                     │ ║
║  │  ┌──────────────────────────────────────────────────────────────┐  │ ║
║  │  │  CopilotAgent (app/copilot/agent.py)                        │  │ ║
║  │  │  • Intent classification                                    │  │ ║
║  │  │  • System prompt building                                   │  │ ║
║  │  │  • Response generation                                      │  │ ║
║  │  │  • Session context management                               │  │ ║
║  │  └────────┬─────────────────────────────────────────────────────┘  │ ║
║  │           │                                                         │ ║
║  │  ┌────────▼────────────┐  ┌──────────────────────────────────────┐  │ ║
║  │  │ ClaudeClient        │  │ SessionManager                       │  │ ║
║  │  │ (services/)         │  │ (services/session_manager.py)        │  │ ║
║  │  │                     │  │                                      │  │ ║
║  │  │ • Call Claude API   │  │ • Create/load sessions               │  │ ║
║  │  │ • Tool calling      │  │ • Store context & history            │  │ ║
║  │  │ • Agentic loop      │  │ • Manage expiration                  │  │ ║
║  │  │ • Error handling    │  │ • In-memory storage (MVP)            │  │ ║
║  │  └────────┬────────────┘  └──────────────────────────────────────┘  │ ║
║  │           │                                                         │ ║
║  └───────────┼─────────────────────────────────────────────────────────┘ ║
║              │                                                           ║
║  ┌───────────▼─────────────────────────────────────────────────────────┐ ║
║  │              MCP Client Manager (mcp/client.py)                     │ ║
║  │                                                                     │ ║
║  │  • Initializes all MCP servers                                     │ ║
║  │  • Routes tool calls to appropriate server                         │ ║
║  │  • Manages tool registry                                           │ ║
║  │  • Converts tool calls between Claude and MCP formats              │ ║
║  └────────────────┬──────────────────┬──────────────────────────────────┘ ║
║                   │                  │                                    ║
║                   │   MCP Protocol   │                                    ║
║                   │                  │                                    ║
╚───────────────────┼──────────────────┼────────────────────────────────────╝
                    │                  │
╔═══════════════════╧══════════════════╧════════════════════════════════════╗
║                      4 SPECIALIZED MCP SERVERS                            ║
║                                                                           ║
║  ┌──────────────────────────┐ ┌──────────────────────────┐               ║
║  │ ApplicationDataMCPServer  │ │   AnalysisMCPServer      │               ║
║  │ (servers/application_    │ │   (servers/analysis.py)  │               ║
║  │  data.py)                │ │                          │               ║
║  │                          │ │ Tools:                   │               ║
║  │ Tools:                   │ │ • analyze_application()  │               ║
║  │ • get_application()      │ │ • compare_applications() │               ║
║  │ • search_applications()  │ │ • generate_report()      │               ║
║  │ • list_applications()    │ │                          │               ║
║  │ • get_application_       │ │ Features:                │               ║
║  │   profiles()             │ │ • Score calculation      │               ║
║  │                          │ │ • Strength analysis      │               ║
║  │ Data Source:             │ │ • Comparison ranking     │               ║
║  │ output/{year}/           │ │ • Report generation      │               ║
║  │ {scholarship}/{app}/     │ │                          │               ║
║  │ *.json files             │ │ Data Source:             │               ║
║  │                          │ │ Uses ApplicationData +   │               ║
║  │                          │ │ heuristic analysis       │               ║
║  └──────────────────────────┘ └──────────────────────────┘               ║
║                                                                           ║
║  ┌──────────────────────────┐ ┌──────────────────────────┐               ║
║  │   ContextMCPServer       │ │ ProcessorMCPServer       │               ║
║  │   (servers/context.py)   │ │ (servers/processor.py)   │               ║
║  │                          │ │                          │               ║
║  │ Tools:                   │ │ Tools:                   │               ║
║  │ • get_context()          │ │ • get_processor_status() │               ║
║  │ • update_context()       │ │ • verify_application_    │               ║
║  │ • get_current_app()      │ │   processed()            │               ║
║  │ • set_current_app()      │ │ • get_step_output()      │               ║
║  │                          │ │                          │               ║
║  │ Storage:                 │ │ Data Source:             │               ║
║  │ In-memory dict           │ │ Processor output paths   │               ║
║  │ {session_id: {...}}      │ │ File existence checks    │               ║
║  │                          │ │                          │               ║
║  │ Future: Database/Redis   │ │                          │               ║
║  └──────────────────────────┘ └──────────────────────────┘               ║
║                                                                           ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │                    ToolRegistry & Schemas                        │   ║
║  │                    (mcp/tools/)                                  │   ║
║  │                                                                  │   ║
║  │  • Maintains registry of all tools across servers               │   ║
║  │  • Provides schemas in Claude API format                        │   ║
║  │  • Validates tool schemas and arguments                         │   ║
║  │  • Tracks server ownership of each tool                         │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
                                   │
                           Claude API Calls
                                   │
╔═══════════════════════════════════╧═════════════════════════════════════╗
║                    CLAUDE OPUS 4.1 (LLM Orchestrator)                  ║
║                                                                         ║
║  • Receives user query + available tools                               ║
║  • Classifies intent                                                   ║
║  • Selects appropriate tools (intelligent tool calling)                ║
║  • Processes tool results                                              ║
║  • Generates natural language response                                 ║
║  • Maintains conversation context                                      ║
║                                                                         ║
║  Response Format:                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │ If tool needed:                                                 │  ║
║  │ {                                                               │  ║
║  │   "type": "tool_use",                                           │  ║
║  │   "name": "get_application",                                    │  ║
║  │   "input": {"app_id": "app_5678"}                               │  ║
║  │ }                                                               │  ║
║  │                                                                 │  ║
║  │ If final response:                                              │  ║
║  │ {                                                               │  ║
║  │   "type": "text",                                               │  ║
║  │   "text": "Based on the analysis, the application shows..."     │  ║
║  │ }                                                               │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                         ║
╚═════════════════════════════════════════════════════════════════════════╝
```

## Data Flow Diagram

```
USER QUERY
    │
    ▼
┌─────────────────────────────────────────┐
│  Frontend: User types message in chat   │
└─────────────────────────────────────────┘
    │
    │ REST API: POST /api/v1/chat
    │ {query: string, session_id: string}
    │
    ▼
┌─────────────────────────────────────────┐
│  FastAPI Route Handler                  │
│  • Validate input                       │
│  • Load session context                 │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  CopilotAgent.process_query()           │
│  • Build system prompt                  │
│  • Get available tools from registry    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  ClaudeClient.chat_with_tools()         │
│  Send to Claude API:                    │
│  {                                      │
│    messages: [...],                     │
│    tools: [...],                        │
│    model: "claude-opus-4-1"             │
│  }                                      │
└─────────────────────────────────────────┘
    │
    │ Claude evaluates tools and generates response
    │
    ▼
┌─────────────────────────────────────────┐
│  Claude Response Processing             │
│                                         │
│  Has tool calls?                        │
│  ├─ YES: Process tool_use blocks        │
│  │        └─ Extract tool name & args   │
│  │           │                          │
│  │           ▼                          │
│  │        MCPClientManager.call_tool()  │
│  │           │                          │
│  │           ▼                          │
│  │        Route to appropriate server   │
│  │           │                          │
│  │           ▼                          │
│  │        MCP Server executes tool      │
│  │           │                          │
│  │           ▼                          │
│  │        Return result to Claude       │
│  │                                      │
│  │        Loop back to Claude with      │
│  │        tool results in context       │
│  │                                      │
│  └─ NO: Extract text response           │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Final Response                         │
│  • Save to session history              │
│  • Update application context           │
│  • Return to frontend                   │
└─────────────────────────────────────────┘
    │
    │ REST API Response
    │ {response: string, session_id, timestamp}
    │
    ▼
┌─────────────────────────────────────────┐
│  Frontend Updates                       │
│  • Display message in chat              │
│  • Update application context sidebar   │
│  • Show loading spinner disappears      │
└─────────────────────────────────────────┘
    │
    ▼
USER SEES RESPONSE
```

## MCP Tool Flow Diagram

```
Claude Decides to Call Tool
    │
    ▼
Tool Call Request
{
  "name": "get_application",
  "input": {"app_id": "app_5678"}
}
    │
    ▼
MCPClientManager.call_tool()
    │
    ├─ Lookup tool in registry
    │  └─ Get server name
    │
    ▼
Determine which MCP Server
    │
    ├─ ApplicationDataMCPServer?
    │  ├─ Read from output/{year}/{scholarship}/{app_id}/*.json
    │  └─ Return application data
    │
    ├─ AnalysisMCPServer?
    │  ├─ Call ApplicationDataMCPServer for data
    │  ├─ Perform analysis/comparison
    │  └─ Return analysis results
    │
    ├─ ContextMCPServer?
    │  ├─ Access in-memory session storage
    │  └─ Return/update context
    │
    └─ ProcessorMCPServer?
       ├─ Check processor output directory
       └─ Return processor status
    │
    ▼
Convert result to JSON string
    │
    ▼
Return to Claude
    │
    ▼
Claude processes result and:
├─ Decides if more tools needed
│  └─ Loop back to tool calling
│
└─ Generates final text response
   └─ Return to user
```

## Component Interaction Diagram

```
                          ┌─────────────────┐
                          │  Frontend UI    │
                          │  (React-like)   │
                          └────────┬────────┘
                                   │ HTTP
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
    ┌─────────┐            ┌────────────┐         ┌──────────────┐
    │ Routes  │◄──────────►│  Services  │         │   Models     │
    │ (api)   │            │ (claude,   │         │  (schemas)   │
    └──┬──────┘            │  session)  │         └──────────────┘
       │                   └──────┬─────┘
       │                          │
       └──────────────┬───────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │  CopilotAgent           │
        │  (Core Logic)           │
        └────────────┬────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐ ┌───────────┐ ┌──────────┐
   │ Claude  │ │ MCP Client│ │ Session  │
   │ Client  │ │ Manager   │ │ Manager  │
   └────┬────┘ └─────┬─────┘ └─────┬────┘
        │            │             │
        │ Claude API │             │
        │            │       ┌─────▼────────┐
        │            │       │ In-Memory    │
        │            │       │ Storage      │
        │            │       └──────────────┘
        │            │
        │            ▼
        │      ┌──────────────────────────┐
        │      │  4 MCP Servers          │
        │      │                          │
        │      │  ┌──────────────────┐   │
        │      │  │ AppDataServer    │   │
        │      │  ├──────────────────┤   │
        │      │  │ AnalysisServer   │   │
        │      │  ├──────────────────┤   │
        │      │  │ ContextServer    │   │
        │      │  ├──────────────────┤   │
        │      │  │ ProcessorServer  │   │
        │      │  └──────────────────┘   │
        │      │         │                │
        │      └─────────┼────────────────┘
        │              │
        └──────────────┼────────────────────
                       │
              ┌────────▼────────┐
              │ External Data   │
              │ & Services      │
              │                 │
              │ • Processor     │
              │   output files  │
              │ • JSON profiles │
              │                 │
              └─────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Environment                     │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  Load Balancer / Nginx                 │    │
│  │  (Routes HTTP/HTTPS traffic, handles SSL/TLS)        │    │
│  └──────────┬─────────────────────────────────┬──────────┘    │
│             │                                 │                │
│  ┌──────────▼─────────┐            ┌──────────▼──────────┐    │
│  │  FastAPI Instance  │            │  FastAPI Instance  │    │
│  │  (Port 8000)       │            │  (Port 8001)       │    │
│  │                    │            │                    │    │
│  │  • MCP Servers     │            │  • MCP Servers     │    │
│  │  • Session Manager │            │  • Session Manager │    │
│  │  • Copilot Agent   │            │  • Copilot Agent   │    │
│  └────────┬───────────┘            └─────────┬──────────┘    │
│           │                                   │                │
└───────────┼───────────────────────────────────┼────────────────┘
            │                                   │
    ┌───────┴──────────┬──────────────┬────────┴─────────┐
    │                  │              │                  │
    ▼                  ▼              ▼                  ▼
┌─────────┐    ┌────────────┐    ┌──────────┐    ┌──────────┐
│ PostgreSQL
│ (Sessions)   │  Shared    │    │ Redis    │    │S3/Files  │
│              │ Processor  │    │(Cache)   │    │(Data)    │
└──────────┘   │ Output     │    └──────────┘    └──────────┘
               │ (Mounted)  │
               └────────────┘

Static Frontend Files (CDN / S3 + CloudFront)
```

## Class Hierarchy Diagram

```
┌─────────────────────────────────────┐
│          MCPServer (Abstract)        │
│                                     │
│ + name: str                         │
│ + initialize()                      │
│ + handle_tool_call()                │
│ + register_tool()                   │
│ + get_tools()                       │
└──────────────────┬──────────────────┘
                   │
       ┌───────────┼───────────┬──────────────────┐
       │           │           │                  │
       ▼           ▼           ▼                  ▼
   ┌────────┐ ┌────────┐ ┌────────┐        ┌─────────┐
   │AppData │ │Analysis│ │Context │        │Processor│
   │Server  │ │Server  │ │Server  │        │Server   │
   └────────┘ └────────┘ └────────┘        └─────────┘

┌─────────────────────────────────────┐
│    FastAPI Application              │
│                                     │
│ + startup_event()                   │
│ + shutdown_event()                  │
│ + exception_handlers                │
│ + include_router()                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    CopilotAgent                     │
│                                     │
│ - claude_client                     │
│ - mcp_client                        │
│ - context_manager                   │
│                                     │
│ + process_query()                   │
│ + _build_system_prompt()            │
│ + _build_messages()                 │
└─────────────────────────────────────┘
```

## Sequence Diagram: Chat Query Processing

```
User      Frontend    FastAPI    Copilot    Claude    MCP       Data
 │          │            │          │         │       Server    Files
 │          │            │          │         │         │         │
 ├─Query───►│            │          │         │         │         │
 │          │            │          │         │         │         │
 │          ├─POST /chat─┼─────────►│         │         │         │
 │          │            │          │         │         │         │
 │          │            │          ├─Build prompt─────►│         │
 │          │            │          │         │         │         │
 │          │            │          ├──────────────────►│         │
 │          │            │          │        Call API   │         │
 │          │            │          │◄──────────────────│         │
 │          │            │          │         │         │         │
 │          │            │          │      Tool call   │         │
 │          │            │          │         │         │         │
 │          │            │          ├─────────┼────────►│         │
 │          │            │          │         │         │         │
 │          │            │          │         │         ├────────►│
 │          │            │          │         │         │ Read    │
 │          │            │          │         │         │ JSON    │
 │          │            │          │         │         │◄────────┤
 │          │            │          │         │         │         │
 │          │            │          │◄────────┼─────────┤         │
 │          │            │          │ Tool result      │         │
 │          │            │          │         │         │         │
 │          │            │          ├──────────────────►│         │
 │          │            │          │ Continue w/       │         │
 │          │            │          │ results           │         │
 │          │            │          │         │         │         │
 │          │            │          │◄──────────────────│         │
 │          │            │          │ Final response    │         │
 │          │            │          │         │         │         │
 │          │◄─Response──┤◄─────────┤         │         │         │
 │          │            │          │         │         │         │
 │◄─Display─┤            │          │         │         │         │
 │          │            │          │         │         │         │
```

This comprehensive architecture documentation provides:

1. **System Overview** - High-level component relationships
2. **Data Flow** - Query processing from user to response
3. **MCP Tool Flow** - How tools are called and executed
4. **Component Interaction** - How different parts communicate
5. **Deployment Architecture** - Production setup
6. **Class Hierarchy** - Object-oriented structure
7. **Sequence Diagram** - Chat request processing timeline

All diagrams use ASCII art for clarity and can be rendered in any text editor or documentation system.
