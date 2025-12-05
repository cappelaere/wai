"""
FastAPI routes for the Scholarship Copilot API.

This module defines all HTTP endpoints for the copilot backend, including:
- Session management (create, read, update, delete)
- Chat interactions
- Tool information
- Health checks
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    SessionResponse,
    SessionDetailResponse,
    ContextRequest,
    ContextUpdateResponse,
    DeleteResponse,
    ToolsResponse,
    ToolSchema,
    HealthResponse,
    ErrorResponse,
)
from app.services.session_manager import SessionManager
from app.services.claude_client import ClaudeClient
from app.mcp.client import MCPClientManager
from app.copilot.agent import CopilotAgent
from app.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["copilot"])

# Global instances (will be initialized in main.py startup)
session_manager: Optional[SessionManager] = None
claude_client: Optional[ClaudeClient] = None
mcp_client: Optional[MCPClientManager] = None
copilot_agent: Optional[CopilotAgent] = None


def get_session_manager() -> SessionManager:
    """
    Dependency to get session manager instance.

    Raises:
        HTTPException: If session manager not initialized
    """
    if session_manager is None:
        logger.error("SessionManager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    return session_manager


def get_copilot_agent() -> CopilotAgent:
    """
    Dependency to get copilot agent instance.

    Raises:
        HTTPException: If copilot agent not initialized
    """
    if copilot_agent is None:
        logger.error("CopilotAgent not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot agent not initialized"
        )
    return copilot_agent


def get_mcp_client() -> MCPClientManager:
    """
    Dependency to get MCP client instance.

    Raises:
        HTTPException: If MCP client not initialized
    """
    if mcp_client is None:
        logger.error("MCPClientManager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP client not initialized"
        )
    return mcp_client


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new conversation session for a user",
    responses={
        201: {"description": "Session created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def create_session(
    request: CreateSessionRequest,
    manager: SessionManager = Depends(get_session_manager)
) -> SessionResponse:
    """
    Create a new conversation session.

    Args:
        request: Request containing user_id
        manager: Session manager instance

    Returns:
        SessionResponse with session_id, created_at, and expires_at

    Raises:
        HTTPException: If session creation fails
    """
    try:
        logger.info(f"Creating session for user {request.user_id}")

        # Create session
        session_id = await manager.create_session(request.user_id)

        # Load session to get timestamps
        session = await manager.load_session(session_id)
        created_at = session["created_at"]
        expires_at = created_at + timedelta(seconds=settings.session_timeout)

        response = SessionResponse(
            session_id=session_id,
            created_at=created_at.isoformat() + "Z",
            expires_at=expires_at.isoformat() + "Z"
        )

        logger.info(f"Successfully created session {session_id}")
        return response

    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Process a user query through the copilot agent",
    responses={
        200: {"description": "Query processed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Processing error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def chat(
    request: ChatRequest,
    agent: CopilotAgent = Depends(get_copilot_agent),
    manager: SessionManager = Depends(get_session_manager)
) -> ChatResponse:
    """
    Process a chat query through the copilot agent.

    Args:
        request: Chat request with query and session_id
        agent: Copilot agent instance
        manager: Session manager instance

    Returns:
        ChatResponse with assistant's response

    Raises:
        HTTPException: If session not found or processing fails
    """
    try:
        logger.info(f"Processing chat for session {request.session_id}")

        # Verify session exists
        try:
            await manager.load_session(request.session_id)
        except ValueError as e:
            logger.warning(f"Session {request.session_id} not found: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found or expired: {request.session_id}"
            )

        # Process query through agent
        response_text = await agent.process_query(
            query=request.query,
            session_id=request.session_id
        )

        # Create response
        response = ChatResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        logger.info(f"Successfully processed chat for session {request.session_id}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details",
    description="Retrieve detailed information about a session",
    responses={
        200: {"description": "Session retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
) -> SessionDetailResponse:
    """
    Get detailed session information.

    Args:
        session_id: Session identifier
        manager: Session manager instance

    Returns:
        SessionDetailResponse with complete session data

    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Retrieving session {session_id}")

        # Load session
        session = await manager.load_session(session_id)

        # Calculate expiration
        expires_at = session["last_accessed"] + timedelta(seconds=settings.session_timeout)

        # Format history (convert datetime to ISO string)
        formatted_history = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat() + "Z"
            }
            for msg in session["history"]
        ]

        response = SessionDetailResponse(
            session_id=session["id"],
            user_id=session["user_id"],
            context=session["context"],
            history=formatted_history,
            created_at=session["created_at"].isoformat() + "Z",
            last_accessed=session["last_accessed"].isoformat() + "Z",
            expires_at=expires_at.isoformat() + "Z"
        )

        logger.info(f"Successfully retrieved session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found or expired: {session_id}"
        )
    except Exception as e:
        logger.error(f"Error retrieving session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.put(
    "/sessions/{session_id}",
    response_model=ContextUpdateResponse,
    summary="Update session context",
    description="Update context data for a session",
    responses={
        200: {"description": "Context updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def update_session_context(
    session_id: str,
    request: ContextRequest,
    manager: SessionManager = Depends(get_session_manager)
) -> ContextUpdateResponse:
    """
    Update session context.

    Args:
        session_id: Session identifier (from path)
        request: Context update request
        manager: Session manager instance

    Returns:
        ContextUpdateResponse indicating success

    Raises:
        HTTPException: If session not found or update fails
    """
    try:
        # Validate session_id matches request
        if session_id != request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID in path does not match request body"
            )

        logger.info(f"Updating context for session {session_id}")

        # Update each context key
        for key, value in request.context.items():
            await manager.update_context(session_id, key, value)

        response = ContextUpdateResponse(
            updated=True,
            session_id=session_id
        )

        logger.info(f"Successfully updated context for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found or expired: {session_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update context: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=DeleteResponse,
    summary="Delete a session",
    description="Delete a session and all its data",
    responses={
        200: {"description": "Session deleted successfully"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
) -> DeleteResponse:
    """
    Delete a session.

    Args:
        session_id: Session identifier
        manager: Session manager instance

    Returns:
        DeleteResponse indicating success

    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Deleting session {session_id}")

        # Delete session
        deleted = await manager.delete_session(session_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )

        response = DeleteResponse(
            deleted=True,
            session_id=session_id
        )

        logger.info(f"Successfully deleted session {session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get(
    "/tools",
    response_model=ToolsResponse,
    summary="Get available tools",
    description="Retrieve list of all available MCP tools",
    responses={
        200: {"description": "Tools retrieved successfully"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def get_tools(
    client: MCPClientManager = Depends(get_mcp_client)
) -> ToolsResponse:
    """
    Get all available MCP tools.

    Args:
        client: MCP client manager instance

    Returns:
        ToolsResponse with list of available tools

    Raises:
        HTTPException: If tools cannot be retrieved
    """
    try:
        logger.info("Retrieving available tools")

        # Get tools from MCP client
        tools_list = client.get_available_tools()

        # Convert to ToolSchema models
        tool_schemas = [
            ToolSchema(
                name=tool["name"],
                description=tool["description"],
                input_schema=tool["input_schema"]
            )
            for tool in tools_list
        ]

        response = ToolsResponse(
            tools=tool_schemas,
            count=len(tool_schemas)
        )

        logger.info(f"Successfully retrieved {len(tool_schemas)} tools")
        return response

    except Exception as e:
        logger.error(f"Error retrieving tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tools: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of all services",
    tags=["health"],
    responses={
        200: {"description": "Service is healthy"},
    }
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse with service status information
    """
    # Check MCP client
    mcp_ready = mcp_client is not None
    if mcp_ready:
        try:
            # Verify MCP client has tools
            tools = mcp_client.get_available_tools()
            mcp_ready = len(tools) > 0
        except Exception as e:
            logger.warning(f"MCP health check failed: {e}")
            mcp_ready = False

    # Check Claude client
    claude_ready = claude_client is not None
    if claude_ready:
        try:
            # Verify API key is set
            claude_ready = bool(claude_client.api_key)
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            claude_ready = False

    # Get session count
    session_count = 0
    if session_manager is not None:
        try:
            session_count = session_manager.get_session_count()
        except Exception as e:
            logger.warning(f"Failed to get session count: {e}")

    # Determine overall status
    overall_status = "healthy" if (mcp_ready and claude_ready) else "degraded"

    response = HealthResponse(
        status=overall_status,
        mcp_ready=mcp_ready,
        claude_ready=claude_ready,
        session_count=session_count,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

    logger.debug(f"Health check: {overall_status}")
    return response


def initialize_dependencies(
    session_mgr: SessionManager,
    claude_cli: ClaudeClient,
    mcp_cli: MCPClientManager,
    copilot_agt: CopilotAgent
):
    """
    Initialize global dependencies.

    This function should be called from main.py during startup.

    Args:
        session_mgr: Initialized SessionManager instance
        claude_cli: Initialized ClaudeClient instance
        mcp_cli: Initialized MCPClientManager instance
        copilot_agt: Initialized CopilotAgent instance
    """
    global session_manager, claude_client, mcp_client, copilot_agent

    session_manager = session_mgr
    claude_client = claude_cli
    mcp_client = mcp_cli
    copilot_agent = copilot_agt

    logger.info("Route dependencies initialized")
