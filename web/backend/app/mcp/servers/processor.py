"""Processor MCP Server.

This server provides tools for checking the status of the application processor
and verifying that applications have been successfully processed. It interacts
with the processor's output directory to verify file existence and completeness.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..servers.base import MCPServer, ToolSchema
from ...config import settings

logger = logging.getLogger(__name__)


class ProcessorMCPServer(MCPServer):
    """MCP Server for monitoring and verifying processor status.

    This server provides tools to:
    - Check processor status and health
    - Verify that applications have been fully processed
    - Get information about processing steps and outputs
    - Monitor processing completeness

    This is a read-only server that checks file system state.
    """

    # Expected profile files for a complete application
    REQUIRED_PROFILES = [
        "application_profile.json",
        "personal_profile.json",
        "academic_profile.json",
        "social_profile.json",
        "recommendation_profile.json"
    ]

    # Optional files that may be present
    OPTIONAL_FILES = [
        "application_form_data.json",
        "attachments.json"
    ]

    def __init__(self):
        """Initialize the Processor MCP Server."""
        super().__init__(
            name="processor",
            description="Monitor and verify application processor status"
        )
        self.output_path = Path(settings.processor_output_path)
        logger.info(f"Processor output path: {self.output_path}")

    async def initialize(self) -> None:
        """Initialize the server and register tools."""
        # Register get_processor_status tool
        self.register_tool(
            ToolSchema(
                name="get_processor_status",
                description="Get the current status and health of the application processor",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                return_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "total_applications": {"type": "integer"},
                        "scholarships": {"type": "array", "items": {"type": "string"}},
                        "output_path": {"type": "string"},
                        "last_processed": {"type": "string", "format": "date-time"}
                    }
                }
            ),
            self._get_processor_status
        )

        # Register verify_application_processed tool
        self.register_tool(
            ToolSchema(
                name="verify_application_processed",
                description="Verify that an application has been fully processed with all required profiles",
                input_schema={
                    "type": "object",
                    "properties": {
                        "application_id": {
                            "type": "string",
                            "description": "Application ID to verify"
                        }
                    },
                    "required": ["application_id"]
                },
                return_schema={
                    "type": "object",
                    "properties": {
                        "application_id": {"type": "string"},
                        "is_processed": {"type": "boolean"},
                        "completeness": {"type": "number"},
                        "missing_files": {"type": "array", "items": {"type": "string"}},
                        "present_files": {"type": "array", "items": {"type": "string"}},
                        "path": {"type": "string"},
                        "total_files": {"type": "integer"},
                        "required_files": {"type": "integer"}
                    }
                }
            ),
            self._verify_application_processed
        )

        # Register get_step_output tool
        self.register_tool(
            ToolSchema(
                name="get_step_output",
                description="Get metadata about a specific processing step output for an application",
                input_schema={
                    "type": "object",
                    "properties": {
                        "application_id": {
                            "type": "string",
                            "description": "Application ID"
                        },
                        "step": {
                            "type": "string",
                            "enum": ["application", "personal", "academic", "social", "recommendation"],
                            "description": "Processing step to check"
                        }
                    },
                    "required": ["application_id", "step"]
                },
                return_schema={
                    "type": "object",
                    "properties": {
                        "application_id": {"type": "string"},
                        "step": {"type": "string"},
                        "exists": {"type": "boolean"},
                        "file_path": {"type": "string"},
                        "file_size": {"type": "integer"},
                        "last_modified": {"type": ["string", "null"], "format": "date-time"}
                    }
                }
            ),
            self._get_step_output
        )

        logger.info("Processor MCP Server initialized with 3 tools")

    def _find_application_path(self, application_id: str) -> Optional[Path]:
        """Find the directory path for a given application ID.

        Args:
            application_id: The application ID to search for

        Returns:
            Path to the application directory if found, None otherwise
        """
        try:
            # Search through scholarship directories
            for year_dir in self.output_path.glob("*"):
                if not year_dir.is_dir() or year_dir.name.startswith('.'):
                    continue

                for scholarship_dir in year_dir.glob("*"):
                    if not scholarship_dir.is_dir() or scholarship_dir.name.startswith('.'):
                        continue

                    app_dir = scholarship_dir / application_id
                    if app_dir.exists() and app_dir.is_dir():
                        return app_dir

            return None
        except Exception as e:
            logger.error(f"Error finding application path: {e}")
            return None

    def _count_applications(self) -> Dict[str, Any]:
        """Count total applications and scholarships.

        Returns:
            Dictionary with counts and scholarship names
        """
        total = 0
        scholarships = set()

        try:
            for year_dir in self.output_path.glob("*"):
                if not year_dir.is_dir() or year_dir.name.startswith('.'):
                    continue

                for scholarship_dir in year_dir.glob("*"):
                    if not scholarship_dir.is_dir() or scholarship_dir.name.startswith('.'):
                        continue

                    scholarships.add(scholarship_dir.name)

                    # Count application directories
                    for app_dir in scholarship_dir.glob("*"):
                        if app_dir.is_dir() and not app_dir.name.startswith('.'):
                            total += 1

            return {
                "total": total,
                "scholarships": sorted(list(scholarships))
            }
        except Exception as e:
            logger.error(f"Error counting applications: {e}")
            return {"total": 0, "scholarships": []}

    async def _get_processor_status(self) -> Dict[str, Any]:
        """Get the current status and health of the processor.

        Returns:
            Dictionary with processor status information
        """
        logger.info("Getting processor status")

        # Check if output directory exists
        if not self.output_path.exists():
            return {
                "status": "offline",
                "total_applications": 0,
                "scholarships": [],
                "output_path": str(self.output_path),
                "error": "Output directory does not exist"
            }

        # Count applications and scholarships
        counts = self._count_applications()

        # Determine status based on presence of applications
        if counts["total"] > 0:
            status = "operational"
        else:
            status = "offline"

        result = {
            "status": status,
            "total_applications": counts["total"],
            "scholarships": counts["scholarships"],
            "last_processed": datetime.now().isoformat(),  # Placeholder
            "output_path": str(self.output_path)
        }

        logger.info(f"Processor status: {status}, {counts['total']} applications")
        return result

    async def _verify_application_processed(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """Verify that an application has been fully processed.

        Args:
            application_id: Application ID to verify

        Returns:
            Dictionary with verification results

        Raises:
            RuntimeError: If application cannot be found
        """
        logger.info(f"Verifying processing status for application: {application_id}")

        # Find application directory
        app_path = self._find_application_path(application_id)

        if not app_path:
            raise RuntimeError(f"Application not found: {application_id}")

        # Check for required profile files
        present_files = []
        missing_files = []

        for profile_file in self.REQUIRED_PROFILES:
            file_path = app_path / profile_file
            if file_path.exists():
                present_files.append(profile_file)
            else:
                missing_files.append(profile_file)

        # Check optional files (don't count as missing)
        for optional_file in self.OPTIONAL_FILES:
            file_path = app_path / optional_file
            if file_path.exists():
                present_files.append(optional_file)

        # Calculate completeness percentage
        total_required = len(self.REQUIRED_PROFILES)
        present_required = len([f for f in present_files if f in self.REQUIRED_PROFILES])
        completeness = (present_required / total_required) * 100 if total_required > 0 else 0

        # Application is considered processed if all required files are present
        is_processed = len(missing_files) == 0

        result = {
            "application_id": application_id,
            "is_processed": is_processed,
            "completeness": completeness,
            "missing_files": missing_files,
            "present_files": present_files,
            "path": str(app_path),
            "total_files": len(present_files),
            "required_files": total_required
        }

        status_msg = "complete" if is_processed else f"incomplete ({completeness:.1f}%)"
        logger.info(f"Application {application_id} is {status_msg}")

        return result

    async def _get_step_output(
        self,
        application_id: str,
        step: str
    ) -> Dict[str, Any]:
        """Get metadata about a specific processing step output.

        Args:
            application_id: Application ID
            step: Processing step (application, personal, academic, social, recommendation)

        Returns:
            Dictionary with step output metadata

        Raises:
            RuntimeError: If application cannot be found
        """
        logger.info(f"Getting step output for {application_id}, step: {step}")

        # Find application directory
        app_path = self._find_application_path(application_id)

        if not app_path:
            raise RuntimeError(f"Application not found: {application_id}")

        # Map step name to file name
        step_file_map = {
            "application": "application_profile.json",
            "personal": "personal_profile.json",
            "academic": "academic_profile.json",
            "social": "social_profile.json",
            "recommendation": "recommendation_profile.json"
        }

        if step not in step_file_map:
            raise RuntimeError(f"Invalid step: {step}")

        file_name = step_file_map[step]
        file_path = app_path / file_name

        # Check if file exists and get metadata
        exists = file_path.exists()

        result = {
            "application_id": application_id,
            "step": step,
            "exists": exists,
            "file_path": str(file_path)
        }

        if exists:
            # Get file metadata
            stat = file_path.stat()
            result["file_size"] = stat.st_size
            result["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        else:
            result["file_size"] = 0
            result["last_modified"] = None

        logger.info(f"Step {step} for {application_id}: exists={exists}")
        return result
