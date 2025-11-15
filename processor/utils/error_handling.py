#!/usr/bin/env python3
"""
Unified error handling and result types for the scholarship processor.

Provides consistent error handling, recovery strategies, and result types
across all processing steps and agents.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Any, Dict
from enum import Enum
import json


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorResult:
    """
    Standardized error result for consistent error handling across all steps.

    Attributes:
        success: Whether the operation succeeded (False for error results)
        severity: Severity level of the error (WARNING, ERROR, CRITICAL)
        message: Human-readable error message
        error_type: Type of error (e.g., "OllamaConnectionError", "FileNotFoundError")
        context: Additional context about where/when error occurred
        details: Optional detailed error information for debugging
        recoverable: Whether the operation can be retried
        source: Which component/step generated the error
    """

    success: bool = False
    severity: ErrorSeverity = ErrorSeverity.ERROR
    message: str = ""
    error_type: str = ""
    context: str = ""
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = False
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling Enum conversion."""
        d = asdict(self)
        d['severity'] = self.severity.value
        return d

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        """String representation for logging."""
        base = f"[{self.severity.value.upper()}] {self.message}"
        if self.context:
            base += f" (Context: {self.context})"
        if self.error_type:
            base += f" [{self.error_type}]"
        return base


@dataclass
class SuccessResult:
    """
    Standardized success result for consistent result handling across all steps.

    Attributes:
        success: Always True for success results
        data: The actual result data
        source: Which component/step generated the result
        notes: Optional notes about the result
    """

    success: bool = True
    data: Optional[Any] = None
    source: str = ""
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'source': self.source,
            'notes': self.notes
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def __str__(self) -> str:
        """String representation for logging."""
        base = "SUCCESS"
        if self.source:
            base += f" [{self.source}]"
        if self.notes:
            base += f": {self.notes}"
        return base


def make_error_result(
    message: str,
    error_type: str = "UnknownError",
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    context: str = "",
    details: Optional[Dict[str, Any]] = None,
    recoverable: bool = False,
    source: str = ""
) -> ErrorResult:
    """
    Convenience function to create an ErrorResult.

    Args:
        message: Human-readable error message
        error_type: Type of error (e.g., "FileNotFoundError", "OllamaConnectionError")
        severity: Severity level of the error
        context: Context about where/when error occurred
        details: Optional detailed error information
        recoverable: Whether the operation can be retried
        source: Which component generated the error

    Returns:
        Configured ErrorResult instance
    """
    return ErrorResult(
        success=False,
        severity=severity,
        message=message,
        error_type=error_type,
        context=context,
        details=details or {},
        recoverable=recoverable,
        source=source
    )


def make_success_result(
    data: Any,
    source: str = "",
    notes: Optional[str] = None
) -> SuccessResult:
    """
    Convenience function to create a SuccessResult.

    Args:
        data: The result data
        source: Which component generated the result
        notes: Optional notes about the result

    Returns:
        Configured SuccessResult instance
    """
    return SuccessResult(
        success=True,
        data=data,
        source=source,
        notes=notes
    )
