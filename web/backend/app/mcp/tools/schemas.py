"""Tool schema definitions for MCP servers.

This module defines the schemas for all tools that can be used across MCP servers.
Each schema includes a name, description, input schema (JSON schema), and return schema.
"""

from typing import Dict, Any


# Application Data Tools

GET_APPLICATION_SCHEMA: Dict[str, Any] = {
    "name": "get_application",
    "description": "Retrieve detailed information about a specific scholarship application by ID",
    "inputSchema": {
        "type": "object",
        "properties": {
            "application_id": {
                "type": "string",
                "description": "Unique identifier for the scholarship application"
            }
        },
        "required": ["application_id"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "student_name": {"type": "string"},
            "email": {"type": "string"},
            "scholarship_name": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["pending", "under_review", "approved", "rejected"]
            },
            "submitted_at": {"type": "string", "format": "date-time"},
            "gpa": {"type": "number"},
            "essay": {"type": "string"},
            "financial_need": {"type": "number"},
            "extracurriculars": {
                "type": "array",
                "items": {"type": "string"}
            },
            "metadata": {"type": "object"}
        },
        "required": ["id", "student_name", "email", "scholarship_name", "status"]
    }
}

SEARCH_APPLICATIONS_SCHEMA: Dict[str, Any] = {
    "name": "search_applications",
    "description": "Search for scholarship applications based on various criteria",
    "inputSchema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "under_review", "approved", "rejected"],
                "description": "Filter by application status"
            },
            "scholarship_name": {
                "type": "string",
                "description": "Filter by scholarship name (partial match supported)"
            },
            "min_gpa": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 4.0,
                "description": "Minimum GPA threshold"
            },
            "max_gpa": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 4.0,
                "description": "Maximum GPA threshold"
            },
            "submitted_after": {
                "type": "string",
                "format": "date-time",
                "description": "Filter applications submitted after this date"
            },
            "submitted_before": {
                "type": "string",
                "format": "date-time",
                "description": "Filter applications submitted before this date"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 10,
                "description": "Maximum number of results to return"
            },
            "offset": {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "Number of results to skip (for pagination)"
            }
        },
        "required": []
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "total": {"type": "integer"},
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "student_name": {"type": "string"},
                        "scholarship_name": {"type": "string"},
                        "status": {"type": "string"},
                        "gpa": {"type": "number"},
                        "submitted_at": {"type": "string"}
                    }
                }
            }
        },
        "required": ["total", "results"]
    }
}

LIST_APPLICATIONS_SCHEMA: Dict[str, Any] = {
    "name": "list_applications",
    "description": "List all scholarship applications with optional pagination",
    "inputSchema": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
                "description": "Maximum number of results to return"
            },
            "offset": {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "Number of results to skip"
            },
            "sort_by": {
                "type": "string",
                "enum": ["submitted_at", "gpa", "student_name"],
                "default": "submitted_at",
                "description": "Field to sort results by"
            },
            "sort_order": {
                "type": "string",
                "enum": ["asc", "desc"],
                "default": "desc",
                "description": "Sort order"
            }
        },
        "required": []
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "total": {"type": "integer"},
            "applications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "student_name": {"type": "string"},
                        "scholarship_name": {"type": "string"},
                        "status": {"type": "string"},
                        "submitted_at": {"type": "string"}
                    }
                }
            }
        },
        "required": ["total", "applications"]
    }
}


# Analysis Tools

COMPARE_APPLICATIONS_SCHEMA: Dict[str, Any] = {
    "name": "compare_applications",
    "description": "Compare multiple scholarship applications side-by-side",
    "inputSchema": {
        "type": "object",
        "properties": {
            "application_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 10,
                "description": "List of application IDs to compare"
            },
            "comparison_criteria": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["gpa", "financial_need", "essay_quality", "extracurriculars", "overall_fit"]
                },
                "default": ["gpa", "financial_need", "essay_quality"],
                "description": "Criteria to use for comparison"
            }
        },
        "required": ["application_ids"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "comparison": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "application_id": {"type": "string"},
                        "student_name": {"type": "string"},
                        "scores": {
                            "type": "object",
                            "additionalProperties": {"type": "number"}
                        },
                        "rank": {"type": "integer"}
                    }
                }
            },
            "summary": {
                "type": "object",
                "properties": {
                    "top_candidate": {"type": "string"},
                    "key_differences": {"type": "array", "items": {"type": "string"}},
                    "recommendation": {"type": "string"}
                }
            }
        },
        "required": ["comparison"]
    }
}

ANALYZE_APPLICATION_SCHEMA: Dict[str, Any] = {
    "name": "analyze_application",
    "description": "Perform detailed analysis on a single scholarship application",
    "inputSchema": {
        "type": "object",
        "properties": {
            "application_id": {
                "type": "string",
                "description": "ID of the application to analyze"
            },
            "analysis_type": {
                "type": "string",
                "enum": ["comprehensive", "essay_only", "qualifications_only", "financial_need"],
                "default": "comprehensive",
                "description": "Type of analysis to perform"
            }
        },
        "required": ["application_id"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "application_id": {"type": "string"},
            "analysis": {
                "type": "object",
                "properties": {
                    "academic_score": {"type": "number"},
                    "essay_score": {"type": "number"},
                    "extracurricular_score": {"type": "number"},
                    "financial_need_score": {"type": "number"},
                    "overall_score": {"type": "number"}
                }
            },
            "strengths": {"type": "array", "items": {"type": "string"}},
            "weaknesses": {"type": "array", "items": {"type": "string"}},
            "recommendation": {
                "type": "string",
                "enum": ["strongly_recommend", "recommend", "consider", "not_recommend"]
            },
            "notes": {"type": "string"}
        },
        "required": ["application_id", "analysis", "recommendation"]
    }
}

GENERATE_REPORT_SCHEMA: Dict[str, Any] = {
    "name": "generate_report",
    "description": "Generate a comprehensive report for one or more applications",
    "inputSchema": {
        "type": "object",
        "properties": {
            "application_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Application IDs to include in the report"
            },
            "report_type": {
                "type": "string",
                "enum": ["summary", "detailed", "comparison"],
                "default": "summary",
                "description": "Type of report to generate"
            },
            "include_recommendations": {
                "type": "boolean",
                "default": True,
                "description": "Whether to include recommendations in the report"
            }
        },
        "required": ["application_ids"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "report_id": {"type": "string"},
            "generated_at": {"type": "string", "format": "date-time"},
            "report_type": {"type": "string"},
            "content": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "applications": {"type": "array"},
                    "recommendations": {"type": "array"}
                }
            },
            "download_url": {"type": "string", "format": "uri"}
        },
        "required": ["report_id", "generated_at", "content"]
    }
}


# Context Management Tools

GET_CONTEXT_SCHEMA: Dict[str, Any] = {
    "name": "get_context",
    "description": "Retrieve the current context for a conversation or session",
    "inputSchema": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session identifier"
            },
            "context_type": {
                "type": "string",
                "enum": ["conversation", "application", "user"],
                "default": "conversation",
                "description": "Type of context to retrieve"
            }
        },
        "required": ["session_id"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "context_type": {"type": "string"},
            "data": {
                "type": "object",
                "additionalProperties": True
            },
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "required": ["session_id", "data"]
    }
}

UPDATE_CONTEXT_SCHEMA: Dict[str, Any] = {
    "name": "update_context",
    "description": "Update or create context for a conversation or session",
    "inputSchema": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session identifier"
            },
            "context_data": {
                "type": "object",
                "additionalProperties": True,
                "description": "Context data to store"
            },
            "merge": {
                "type": "boolean",
                "default": True,
                "description": "Whether to merge with existing context or replace it"
            }
        },
        "required": ["session_id", "context_data"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "updated": {"type": "boolean"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "required": ["session_id", "updated"]
    }
}


# Statistics and Aggregation Tools

GET_STATISTICS_SCHEMA: Dict[str, Any] = {
    "name": "get_statistics",
    "description": "Get statistical insights about scholarship applications",
    "inputSchema": {
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "enum": [
                    "total_applications",
                    "approval_rate",
                    "average_gpa",
                    "financial_need_distribution",
                    "application_trends"
                ],
                "description": "Statistical metric to retrieve"
            },
            "time_period": {
                "type": "string",
                "enum": ["last_week", "last_month", "last_quarter", "last_year", "all_time"],
                "default": "all_time",
                "description": "Time period for the statistics"
            },
            "group_by": {
                "type": "string",
                "enum": ["scholarship", "status", "date"],
                "description": "How to group the results"
            }
        },
        "required": ["metric"]
    },
    "returnSchema": {
        "type": "object",
        "properties": {
            "metric": {"type": "string"},
            "time_period": {"type": "string"},
            "value": {
                "oneOf": [
                    {"type": "number"},
                    {"type": "object"},
                    {"type": "array"}
                ]
            },
            "breakdown": {
                "type": "object",
                "additionalProperties": True
            },
            "calculated_at": {"type": "string", "format": "date-time"}
        },
        "required": ["metric", "value"]
    }
}


# Utility function to get all schemas
def get_all_schemas() -> Dict[str, Dict[str, Any]]:
    """Get all available tool schemas.

    Returns:
        Dictionary mapping schema names to their definitions
    """
    return {
        "get_application": GET_APPLICATION_SCHEMA,
        "search_applications": SEARCH_APPLICATIONS_SCHEMA,
        "list_applications": LIST_APPLICATIONS_SCHEMA,
        "compare_applications": COMPARE_APPLICATIONS_SCHEMA,
        "analyze_application": ANALYZE_APPLICATION_SCHEMA,
        "generate_report": GENERATE_REPORT_SCHEMA,
        "get_context": GET_CONTEXT_SCHEMA,
        "update_context": UPDATE_CONTEXT_SCHEMA,
        "get_statistics": GET_STATISTICS_SCHEMA,
    }


def get_schemas_by_category() -> Dict[str, list[str]]:
    """Get schemas organized by category.

    Returns:
        Dictionary mapping category names to lists of schema names
    """
    return {
        "application_data": [
            "get_application",
            "search_applications",
            "list_applications",
        ],
        "analysis": [
            "compare_applications",
            "analyze_application",
            "generate_report",
        ],
        "context": [
            "get_context",
            "update_context",
        ],
        "statistics": [
            "get_statistics",
        ],
    }


def validate_schema(schema: Dict[str, Any]) -> bool:
    """Validate that a schema has all required fields.

    Args:
        schema: Schema to validate

    Returns:
        True if schema is valid, False otherwise
    """
    required_fields = ["name", "description", "inputSchema", "returnSchema"]
    return all(field in schema for field in required_fields)
