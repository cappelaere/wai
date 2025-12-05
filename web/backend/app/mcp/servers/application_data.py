"""Application Data MCP Server.

This server provides tools for accessing scholarship application data from the
processor output directory. It handles loading and querying application profiles,
metadata, and related information.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..servers.base import MCPServer, ToolSchema
from ..tools.schemas import (
    GET_APPLICATION_SCHEMA,
    LIST_APPLICATIONS_SCHEMA,
    SEARCH_APPLICATIONS_SCHEMA,
)
from ...config import settings

logger = logging.getLogger(__name__)


class ApplicationDataMCPServer(MCPServer):
    """MCP Server for accessing scholarship application data.

    This server provides tools to:
    - Retrieve individual applications by ID
    - Search applications based on criteria
    - List applications with pagination
    - Access application profiles (personal, academic, social, etc.)

    Data is loaded from JSON files in the processor output directory.
    """

    def __init__(self):
        """Initialize the Application Data MCP Server."""
        super().__init__(
            name="application_data",
            description="Access and query scholarship application data"
        )
        self.output_path = Path(settings.processor_output_path)
        logger.info(f"Application data path: {self.output_path}")

    async def initialize(self) -> None:
        """Initialize the server and register tools."""
        # Helper function to convert schema from camelCase to snake_case keys
        def convert_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "name": schema["name"],
                "description": schema["description"],
                "input_schema": schema["inputSchema"],
                "return_schema": schema["returnSchema"]
            }

        # Register get_application tool
        self.register_tool(
            ToolSchema(**convert_schema(GET_APPLICATION_SCHEMA)),
            self._get_application
        )

        # Register search_applications tool
        self.register_tool(
            ToolSchema(**convert_schema(SEARCH_APPLICATIONS_SCHEMA)),
            self._search_applications
        )

        # Register list_applications tool
        self.register_tool(
            ToolSchema(**convert_schema(LIST_APPLICATIONS_SCHEMA)),
            self._list_applications
        )

        logger.info("Application Data MCP Server initialized with 3 tools")

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
                if not year_dir.is_dir():
                    continue

                for scholarship_dir in year_dir.glob("*"):
                    if not scholarship_dir.is_dir():
                        continue

                    app_dir = scholarship_dir / application_id
                    if app_dir.exists() and app_dir.is_dir():
                        return app_dir

            return None
        except Exception as e:
            logger.error(f"Error finding application path: {e}")
            return None

    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Parsed JSON data as dict, or None if file doesn't exist or is invalid
        """
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def _get_all_application_ids(self) -> List[Dict[str, str]]:
        """Get all application IDs with their scholarship and year info.

        Returns:
            List of dicts containing application_id, scholarship_name, and year
        """
        applications = []

        try:
            for year_dir in self.output_path.glob("*"):
                if not year_dir.is_dir() or year_dir.name.startswith('.'):
                    continue

                year = year_dir.name

                for scholarship_dir in year_dir.glob("*"):
                    if not scholarship_dir.is_dir() or scholarship_dir.name.startswith('.'):
                        continue

                    scholarship_name = scholarship_dir.name

                    for app_dir in scholarship_dir.glob("*"):
                        if not app_dir.is_dir() or app_dir.name.startswith('.'):
                            continue

                        applications.append({
                            "application_id": app_dir.name,
                            "scholarship_name": scholarship_name,
                            "year": year,
                            "path": str(app_dir)
                        })

            return applications
        except Exception as e:
            logger.error(f"Error getting application IDs: {e}")
            return []

    async def _get_application(self, application_id: str) -> Dict[str, Any]:
        """Retrieve detailed information about a specific application.

        Args:
            application_id: Unique identifier for the scholarship application

        Returns:
            Dictionary containing application data and all profiles

        Raises:
            RuntimeError: If application is not found or data cannot be loaded
        """
        logger.info(f"Getting application: {application_id}")

        app_path = self._find_application_path(application_id)
        if not app_path:
            raise RuntimeError(f"Application not found: {application_id}")

        # Load all profile files
        profiles = {}
        profile_files = [
            "application_profile.json",
            "personal_profile.json",
            "academic_profile.json",
            "social_profile.json",
            "recommendation_profile.json"
        ]

        for profile_file in profile_files:
            profile_data = self._load_json_file(app_path / profile_file)
            if profile_data:
                profile_name = profile_file.replace(".json", "")
                profiles[profile_name] = profile_data

        # Load application form data if available
        form_data = self._load_json_file(app_path / "application_form_data.json")

        # Load attachments metadata if available
        attachments = self._load_json_file(app_path / "attachments.json")

        # Construct the response
        result = {
            "id": application_id,
            "profiles": profiles,
            "form_data": form_data,
            "attachments": attachments,
            "path": str(app_path),
            "scholarship_name": app_path.parent.name,
            "year": app_path.parent.parent.name
        }

        # Extract key fields from application profile if available
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]

            # Extract basic info
            if "profile" in app_profile:
                profile_info = app_profile["profile"]
                result["student_name"] = f"{profile_info.get('first_name', '')} {profile_info.get('last_name', '')}".strip()
                result["email"] = profile_info.get("email", "")
                result["wai_membership_number"] = profile_info.get("wai_membership_number", "")

            # Extract scores
            if "total_score_summary" in app_profile:
                result["scores"] = app_profile["total_score_summary"]

            # Add summary if available
            if "summary" in app_profile:
                result["summary"] = app_profile["summary"]

        # Set default status (could be enhanced later)
        result["status"] = "pending"
        result["submitted_at"] = datetime.now().isoformat()

        logger.info(f"Successfully loaded application {application_id} with {len(profiles)} profiles")
        return result

    async def _search_applications(
        self,
        status: Optional[str] = None,
        scholarship_name: Optional[str] = None,
        min_gpa: Optional[float] = None,
        max_gpa: Optional[float] = None,
        submitted_after: Optional[str] = None,
        submitted_before: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search for applications based on various criteria.

        Args:
            status: Filter by application status
            scholarship_name: Filter by scholarship name (partial match)
            min_gpa: Minimum GPA threshold
            max_gpa: Maximum GPA threshold
            submitted_after: Filter applications submitted after this date
            submitted_before: Filter applications submitted before this date
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Dictionary with total count and matching applications
        """
        logger.info(f"Searching applications with filters: status={status}, scholarship={scholarship_name}")

        all_apps = self._get_all_application_ids()
        matched_apps = []

        for app_info in all_apps:
            # Apply scholarship name filter
            if scholarship_name and scholarship_name.lower() not in app_info["scholarship_name"].lower():
                continue

            # Load application profile to check other criteria
            app_path = Path(app_info["path"])
            app_profile = self._load_json_file(app_path / "application_profile.json")

            if not app_profile:
                continue

            # Extract GPA if available (from academic profile)
            gpa = None
            if "academic_profile" in app_profile:
                academic = app_profile["academic_profile"]
                if "profile_features" in academic:
                    perf = academic["profile_features"].get("academic_performance", {})
                    gpa = perf.get("gpa")

            # Apply GPA filters
            if min_gpa is not None and (gpa is None or gpa < min_gpa):
                continue
            if max_gpa is not None and (gpa is None or gpa > max_gpa):
                continue

            # Build result entry
            result_entry = {
                "id": app_info["application_id"],
                "scholarship_name": app_info["scholarship_name"],
                "status": "pending",  # Default status
                "submitted_at": datetime.now().isoformat()
            }

            # Add student name if available
            if "profile" in app_profile:
                profile_info = app_profile["profile"]
                result_entry["student_name"] = f"{profile_info.get('first_name', '')} {profile_info.get('last_name', '')}".strip()

            # Add GPA if available
            if gpa is not None:
                result_entry["gpa"] = gpa

            # Add scores if available
            if "total_score_summary" in app_profile:
                scores = app_profile["total_score_summary"]
                result_entry["overall_score"] = scores.get("total_score", 0)
                result_entry["percentage"] = scores.get("percentage", 0)

            matched_apps.append(result_entry)

        # Apply pagination
        total = len(matched_apps)
        paginated_apps = matched_apps[offset:offset + limit]

        logger.info(f"Found {total} applications matching criteria, returning {len(paginated_apps)}")

        return {
            "total": total,
            "results": paginated_apps,
            "limit": limit,
            "offset": offset
        }

    async def _list_applications(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "submitted_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List all applications with pagination and sorting.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            sort_by: Field to sort by (submitted_at, gpa, student_name)
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with total count and list of applications
        """
        logger.info(f"Listing applications: limit={limit}, offset={offset}, sort_by={sort_by}")

        all_apps = self._get_all_application_ids()
        applications = []

        for app_info in all_apps:
            app_path = Path(app_info["path"])
            app_profile = self._load_json_file(app_path / "application_profile.json")

            if not app_profile:
                continue

            # Build application entry
            entry = {
                "id": app_info["application_id"],
                "scholarship_name": app_info["scholarship_name"],
                "status": "pending",
                "submitted_at": datetime.now().isoformat(),
                "year": app_info["year"]
            }

            # Add student name
            if "profile" in app_profile:
                profile_info = app_profile["profile"]
                student_name = f"{profile_info.get('first_name', '')} {profile_info.get('last_name', '')}".strip()
                entry["student_name"] = student_name or "Unknown"
            else:
                entry["student_name"] = "Unknown"

            # Add GPA if available
            if "academic_profile" in app_profile:
                academic = app_profile["academic_profile"]
                if "profile_features" in academic:
                    perf = academic["profile_features"].get("academic_performance", {})
                    gpa = perf.get("gpa")
                    if gpa is not None:
                        entry["gpa"] = gpa

            # Add scores
            if "total_score_summary" in app_profile:
                scores = app_profile["total_score_summary"]
                entry["overall_score"] = scores.get("total_score", 0)
                entry["percentage"] = scores.get("percentage", 0)

            applications.append(entry)

        # Sort applications
        reverse = (sort_order == "desc")
        if sort_by == "student_name":
            applications.sort(key=lambda x: x.get("student_name", ""), reverse=reverse)
        elif sort_by == "gpa":
            applications.sort(key=lambda x: x.get("gpa", 0), reverse=reverse)
        else:  # submitted_at
            applications.sort(key=lambda x: x.get("submitted_at", ""), reverse=reverse)

        # Apply pagination
        total = len(applications)
        paginated = applications[offset:offset + limit]

        logger.info(f"Listed {len(paginated)} of {total} total applications")

        return {
            "total": total,
            "applications": paginated,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
