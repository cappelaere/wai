"""
Pydantic models for request/response validation.

This module defines all the request and response schemas used by the FastAPI
endpoints. Provides type validation, serialization, and documentation.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """
    Request schema for chat endpoint.

    Attributes:
        query: User's question or request
        session_id: Unique identifier for the conversation session
    """

    query: str = Field(
        ...,
        description="User's question or request",
        min_length=1,
        max_length=10000,
        examples=["What are the top 3 candidates?"]
    )
    session_id: str = Field(
        ...,
        description="Session ID for conversation context",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate that query is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or only whitespace")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Who are the top candidates for the scholarship?",
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Response schema for chat endpoint.

    Attributes:
        response: AI assistant's response text
        session_id: Session ID for this interaction
        timestamp: ISO 8601 formatted timestamp
    """

    response: str = Field(
        ...,
        description="AI assistant's response",
        examples=["Based on the analysis, the top 3 candidates are..."]
    )
    session_id: str = Field(
        ...,
        description="Session ID for this interaction",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 formatted timestamp",
        examples=["2025-11-15T10:30:00.000Z"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Based on the analysis, the top 3 candidates are: Alice Johnson, Bob Smith, and Carol White.",
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "timestamp": "2025-11-15T10:30:00.000Z"
                }
            ]
        }
    }


class CreateSessionRequest(BaseModel):
    """
    Request schema for creating a new session.

    Attributes:
        user_id: Unique identifier for the user
    """

    user_id: str = Field(
        ...,
        description="Unique identifier for the user",
        min_length=1,
        max_length=255,
        examples=["user123"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user123"
                }
            ]
        }
    }


class SessionResponse(BaseModel):
    """
    Response schema for session creation and retrieval.

    Attributes:
        session_id: Unique session identifier (UUID)
        created_at: ISO 8601 formatted creation timestamp
        expires_at: ISO 8601 formatted expiration timestamp
    """

    session_id: str = Field(
        ...,
        description="Unique session identifier (UUID)",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 formatted creation timestamp",
        examples=["2025-11-15T10:00:00.000Z"]
    )
    expires_at: str = Field(
        ...,
        description="ISO 8601 formatted expiration timestamp",
        examples=["2025-11-15T11:00:00.000Z"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "created_at": "2025-11-15T10:00:00.000Z",
                    "expires_at": "2025-11-15T11:00:00.000Z"
                }
            ]
        }
    }


class SessionDetailResponse(BaseModel):
    """
    Detailed session information response.

    Attributes:
        session_id: Unique session identifier
        user_id: User who owns this session
        context: Session context dictionary
        history: Conversation history
        created_at: ISO 8601 creation timestamp
        last_accessed: ISO 8601 last access timestamp
        expires_at: ISO 8601 expiration timestamp
    """

    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session context data"
    )
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation history"
    )
    created_at: str = Field(..., description="Creation timestamp")
    last_accessed: str = Field(..., description="Last access timestamp")
    expires_at: str = Field(..., description="Expiration timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "user_id": "user123",
                    "context": {
                        "current_application": "app456",
                        "preferences": {}
                    },
                    "history": [
                        {
                            "role": "user",
                            "content": "Show me the top candidates",
                            "timestamp": "2025-11-15T10:15:00.000Z"
                        },
                        {
                            "role": "assistant",
                            "content": "Based on the analysis...",
                            "timestamp": "2025-11-15T10:15:05.000Z"
                        }
                    ],
                    "created_at": "2025-11-15T10:00:00.000Z",
                    "last_accessed": "2025-11-15T10:30:00.000Z",
                    "expires_at": "2025-11-15T11:00:00.000Z"
                }
            ]
        }
    }


class ContextRequest(BaseModel):
    """
    Request schema for updating session context.

    Attributes:
        session_id: Session identifier
        context: Dictionary of context key-value pairs to update
    """

    session_id: str = Field(
        ...,
        description="Session identifier",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )
    context: Dict[str, Any] = Field(
        ...,
        description="Context data to update",
        examples=[{"current_application": "app123"}]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "context": {
                        "current_application": "app123",
                        "preferences": {
                            "sort_by": "gpa"
                        }
                    }
                }
            ]
        }
    }


class ContextUpdateResponse(BaseModel):
    """
    Response schema for context update operations.

    Attributes:
        updated: Whether the update was successful
        session_id: Session that was updated
    """

    updated: bool = Field(
        ...,
        description="Whether the update was successful",
        examples=[True]
    )
    session_id: str = Field(
        ...,
        description="Session ID that was updated",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "updated": True,
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
                }
            ]
        }
    }


class DeleteResponse(BaseModel):
    """
    Response schema for delete operations.

    Attributes:
        deleted: Whether the deletion was successful
        session_id: Session that was deleted
    """

    deleted: bool = Field(
        ...,
        description="Whether the deletion was successful",
        examples=[True]
    )
    session_id: str = Field(
        ...,
        description="Session ID that was deleted",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "deleted": True,
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
                }
            ]
        }
    }


class ToolSchema(BaseModel):
    """
    Schema for a single tool definition.

    Attributes:
        name: Tool name
        description: What the tool does
        input_schema: JSON schema for tool inputs
    """
    model_config = {"populate_by_name": True}

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for inputs", alias="inputSchema")


class ToolsResponse(BaseModel):
    """
    Response schema for available tools.

    Attributes:
        tools: List of available tool schemas
        count: Total number of tools
    """

    tools: List[ToolSchema] = Field(
        ...,
        description="List of available tools"
    )
    count: int = Field(
        ...,
        description="Total number of tools",
        examples=[10]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tools": [
                        {
                            "name": "get_application",
                            "description": "Retrieve detailed information about a specific application",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "application_id": {
                                        "type": "string",
                                        "description": "ID of the application"
                                    }
                                },
                                "required": ["application_id"]
                            }
                        }
                    ],
                    "count": 1
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """
    Response schema for health check endpoint.

    Attributes:
        status: Overall health status
        mcp_ready: Whether MCP client is initialized
        claude_ready: Whether Claude client is ready
        session_count: Number of active sessions
        timestamp: Current server timestamp
    """

    status: str = Field(
        ...,
        description="Overall health status",
        examples=["healthy"]
    )
    mcp_ready: bool = Field(
        ...,
        description="Whether MCP client is initialized",
        examples=[True]
    )
    claude_ready: bool = Field(
        ...,
        description="Whether Claude client is ready",
        examples=[True]
    )
    session_count: int = Field(
        ...,
        description="Number of active sessions",
        examples=[5]
    )
    timestamp: str = Field(
        ...,
        description="Current server timestamp (ISO 8601)",
        examples=["2025-11-15T10:30:00.000Z"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "mcp_ready": True,
                    "claude_ready": True,
                    "session_count": 5,
                    "timestamp": "2025-11-15T10:30:00.000Z"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """
    Response schema for error responses.

    Attributes:
        error: Error message
        code: Error code
        details: Additional error details
    """

    error: str = Field(
        ...,
        description="Error message",
        examples=["Session not found"]
    )
    code: str = Field(
        ...,
        description="Error code",
        examples=["SESSION_NOT_FOUND"]
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
        examples=[{"session_id": "invalid-id"}]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "Session not found",
                    "code": "SESSION_NOT_FOUND",
                    "details": {
                        "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
                    }
                },
                {
                    "error": "Invalid query format",
                    "code": "VALIDATION_ERROR",
                    "details": {
                        "field": "query",
                        "message": "Query cannot be empty"
                    }
                }
            ]
        }
    }
