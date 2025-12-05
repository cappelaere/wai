"""
FastAPI Application Entry Point.

This module initializes and configures the FastAPI application for the
Scholarship Copilot backend. It sets up:
- CORS middleware
- Logging configuration
- Service initialization (MCP, Claude, Session Manager, Copilot Agent)
- API routes
- Exception handlers
- Startup/shutdown events
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.services.session_manager import SessionManager
from app.services.claude_client import ClaudeClient
from app.mcp.client import MCPClientManager
from app.copilot.agent import CopilotAgent
from app.api import routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global service instances
session_manager: SessionManager = None
claude_client: ClaudeClient = None
mcp_client: MCPClientManager = None
copilot_agent: CopilotAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting Scholarship Copilot Backend")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    try:
        # Initialize services
        await initialize_services()
        logger.info("All services initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

    finally:
        # Shutdown
        logger.info("Shutting down Scholarship Copilot Backend")
        await cleanup_services()
        logger.info("Shutdown complete")


async def initialize_services():
    """
    Initialize all backend services.

    This function:
    1. Creates SessionManager instance
    2. Initializes MCP client and connects to all servers
    3. Initializes Claude client
    4. Creates CopilotAgent with all dependencies
    5. Initializes route dependencies
    """
    global session_manager, claude_client, mcp_client, copilot_agent

    logger.info("Initializing services...")

    # 1. Initialize Session Manager
    logger.info("Initializing SessionManager...")
    session_manager = SessionManager(session_timeout=settings.session_timeout)
    logger.info("SessionManager initialized")

    # 2. Initialize MCP Client
    logger.info("Initializing MCP Client...")
    mcp_client = MCPClientManager()
    await mcp_client.initialize()
    logger.info(f"MCP Client initialized with {len(mcp_client.get_available_tools())} tools")

    # 3. Initialize Claude Client
    logger.info("Initializing Claude Client...")
    claude_client = ClaudeClient(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens
    )
    logger.info(f"Claude Client initialized with model: {settings.claude_model}")

    # 4. Initialize Copilot Agent
    logger.info("Initializing CopilotAgent...")
    copilot_agent = CopilotAgent(
        claude_client=claude_client,
        mcp_client=mcp_client,
        context_manager=session_manager
    )
    logger.info("CopilotAgent initialized")

    # 5. Initialize route dependencies
    logger.info("Initializing route dependencies...")
    routes.initialize_dependencies(
        session_mgr=session_manager,
        claude_cli=claude_client,
        mcp_cli=mcp_client,
        copilot_agt=copilot_agent
    )
    logger.info("Route dependencies initialized")


async def cleanup_services():
    """
    Cleanup services during shutdown.

    Performs cleanup tasks such as:
    - Cleaning up expired sessions
    - Closing database connections (future)
    - Shutting down MCP servers (future)
    """
    global session_manager

    logger.info("Cleaning up services...")

    # Cleanup expired sessions
    if session_manager:
        try:
            deleted_count = await session_manager.cleanup_expired()
            logger.info(f"Cleaned up {deleted_count} expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")

    # Add more cleanup tasks here as needed
    # - Close database connections
    # - Shutdown MCP servers
    # - etc.

    logger.info("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="Scholarship Copilot API",
    description="""
    AI-powered copilot for analyzing scholarship applications.

    This API provides intelligent analysis of scholarship applications using
    Claude AI and Model Context Protocol (MCP) tools. Features include:

    - **Session Management**: Create and manage conversation sessions
    - **Chat Interface**: Natural language querying of application data
    - **Context Awareness**: Maintain conversation context and history
    - **Tool Integration**: Access to MCP tools for data retrieval and analysis
    - **Health Monitoring**: Service health and status endpoints

    ## Authentication

    Currently in MVP phase without authentication. Future versions will include
    user authentication and authorization.

    ## Rate Limiting

    No rate limiting in MVP. Will be added in production.

    ## Websocket Support

    Websocket endpoints available for real-time chat at `/ws/chat`.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Include API routes
app.include_router(routes.router)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.

    Returns a formatted error response with validation details.
    """
    logger.warning(f"Validation error: {exc.errors()}")

    errors = exc.errors()
    error_details = []

    for error in errors:
        error_details.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "code": "VALIDATION_ERROR",
            "details": {
                "errors": error_details
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Handle ValueError exceptions.

    Returns a 400 Bad Request with error details.
    """
    logger.warning(f"ValueError: {exc}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": str(exc),
            "code": "VALIDATION_ERROR",
            "details": {}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle uncaught exceptions.

    Returns a 500 Internal Server Error with error details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal error details in production
    error_detail = str(exc) if settings.debug else "Internal server error"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_detail,
            "code": "INTERNAL_ERROR",
            "details": {}
        }
    )


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="Root endpoint",
    description="Returns API information and status"
)
async def root():
    """
    Root endpoint.

    Returns basic API information.
    """
    return {
        "name": "Scholarship Copilot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Additional health check at root level
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Simple health check endpoint"
)
async def health():
    """
    Simple health check endpoint.

    Returns service status.
    """
    return {
        "status": "healthy",
        "service": "scholarship-copilot-api"
    }


if __name__ == "__main__":
    """
    Run the application directly with uvicorn.

    For development only. In production, use:
        uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    logger.info("Starting development server...")

    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
