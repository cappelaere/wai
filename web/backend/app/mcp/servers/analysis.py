"""Analysis MCP Server.

This server provides tools for analyzing scholarship applications, comparing
multiple applications, and generating reports with insights and recommendations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..servers.base import MCPServer, ToolSchema
from ..tools.schemas import (
    ANALYZE_APPLICATION_SCHEMA,
    COMPARE_APPLICATIONS_SCHEMA,
    GENERATE_REPORT_SCHEMA,
)
from .application_data import ApplicationDataMCPServer

logger = logging.getLogger(__name__)


class AnalysisMCPServer(MCPServer):
    """MCP Server for analyzing scholarship applications.

    This server provides tools to:
    - Analyze individual applications (strengths, weaknesses, scores)
    - Compare multiple applications side-by-side
    - Generate comprehensive reports

    It builds on top of ApplicationDataMCPServer to access application data.
    """

    def __init__(self, data_server: Optional["ApplicationDataMCPServer"] = None):
        """Initialize the Analysis MCP Server.

        Args:
            data_server: Optional ApplicationDataMCPServer instance to use for data access.
                        If None, a new instance will be created.
        """
        super().__init__(
            name="analysis",
            description="Analyze and compare scholarship applications"
        )
        self.data_server = data_server or ApplicationDataMCPServer()

    async def initialize(self) -> None:
        """Initialize the server and register tools."""
        # Ensure data server is initialized (only if not already initialized)
        if not self.data_server._initialized:
            await self.data_server.initialize()
            self.data_server._initialized = True

        # Helper function to convert schema from camelCase to snake_case keys
        def convert_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "name": schema["name"],
                "description": schema["description"],
                "input_schema": schema["inputSchema"],
                "return_schema": schema["returnSchema"]
            }

        # Register analyze_application tool
        self.register_tool(
            ToolSchema(**convert_schema(ANALYZE_APPLICATION_SCHEMA)),
            self._analyze_application
        )

        # Register compare_applications tool
        self.register_tool(
            ToolSchema(**convert_schema(COMPARE_APPLICATIONS_SCHEMA)),
            self._compare_applications
        )

        # Register generate_report tool
        self.register_tool(
            ToolSchema(**convert_schema(GENERATE_REPORT_SCHEMA)),
            self._generate_report
        )

        logger.info("Analysis MCP Server initialized with 3 tools")

    def _calculate_scores(self, app_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate analysis scores from application data.

        Args:
            app_data: Application data dictionary

        Returns:
            Dictionary with calculated scores
        """
        scores = {
            "academic_score": 0.0,
            "essay_score": 0.0,
            "extracurricular_score": 0.0,
            "financial_need_score": 0.0,
            "overall_score": 0.0
        }

        profiles = app_data.get("profiles", {})

        # Extract scores from application profile
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]

            # Get individual profile scores
            if "personal_profile" in app_profile:
                personal = app_profile["personal_profile"]
                if "scores" in personal:
                    scores["essay_score"] = personal["scores"].get("overall_score", 0)

            if "academic_profile" in app_profile:
                academic = app_profile["academic_profile"]
                if "scores" in academic:
                    scores["academic_score"] = academic["scores"].get("overall_score", 0)

            if "social_profile" in app_profile:
                social = app_profile["social_profile"]
                if "scores" in social:
                    scores["extracurricular_score"] = social["scores"].get("overall_score", 0)

            # Calculate overall score from total_score_summary
            if "total_score_summary" in app_profile:
                summary = app_profile["total_score_summary"]
                # Normalize to 0-100 scale
                percentage = summary.get("percentage", 0)
                scores["overall_score"] = percentage

            # Financial need is harder to assess, use a default
            scores["financial_need_score"] = 50.0

        return scores

    def _identify_strengths(self, app_data: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify application strengths based on data and scores.

        Args:
            app_data: Application data dictionary
            scores: Calculated scores

        Returns:
            List of strength descriptions
        """
        strengths = []
        profiles = app_data.get("profiles", {})

        # Check for high academic performance
        if scores["academic_score"] >= 80:
            strengths.append("Strong academic performance and credentials")

        # Check for strong recommendations
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]
            if "recommendation_profile" in app_profile:
                rec = app_profile["recommendation_profile"]
                if "scores" in rec and rec["scores"].get("overall_score", 0) >= 85:
                    strengths.append("Excellent letters of recommendation with specific examples")

        # Check for personal motivation
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]
            if "personal_profile" in app_profile:
                personal = app_profile["personal_profile"]
                if "scores" in personal and personal["scores"].get("motivation_score", 0) >= 85:
                    strengths.append("Clear passion and motivation for aviation career")

        # Check for leadership and community involvement
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]
            if "personal_profile" in app_profile:
                personal = app_profile["personal_profile"]
                features = personal.get("profile_features", {})
                if features.get("leadership_roles"):
                    strengths.append("Demonstrated leadership experience")

        # Check overall score
        if scores["overall_score"] >= 85:
            strengths.append("Exceptionally well-rounded application")

        return strengths if strengths else ["Application shows potential for growth"]

    def _identify_weaknesses(self, app_data: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify application weaknesses based on data and scores.

        Args:
            app_data: Application data dictionary
            scores: Calculated scores

        Returns:
            List of weakness descriptions
        """
        weaknesses = []
        profiles = app_data.get("profiles", {})

        # Check for low academic scores
        if scores["academic_score"] < 60:
            weaknesses.append("Limited academic information or credentials provided")

        # Check for missing school information
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]
            if "profile" in app_profile:
                school_info = app_profile["profile"].get("school_information", {})
                if not school_info.get("school_name"):
                    weaknesses.append("Missing or incomplete school information")

        # Check for goal clarity
        if "application_profile" in profiles:
            app_profile = profiles["application_profile"]
            if "personal_profile" in app_profile:
                personal = app_profile["personal_profile"]
                if "scores" in personal and personal["scores"].get("goals_clarity_score", 100) < 70:
                    weaknesses.append("Career goals could be more specific and detailed")

        # Check overall score
        if scores["overall_score"] < 70:
            weaknesses.append("Application could benefit from stronger overall presentation")

        return weaknesses if weaknesses else ["No significant weaknesses identified"]

    async def _analyze_application(
        self,
        application_id: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Perform detailed analysis on a single application.

        Args:
            application_id: ID of the application to analyze
            analysis_type: Type of analysis (comprehensive, essay_only, etc.)

        Returns:
            Dictionary containing analysis results

        Raises:
            RuntimeError: If application cannot be loaded or analyzed
        """
        logger.info(f"Analyzing application: {application_id} (type: {analysis_type})")

        # Get application data
        try:
            app_data = await self.data_server._get_application(application_id)
        except Exception as e:
            raise RuntimeError(f"Failed to load application: {e}")

        # Calculate scores
        scores = self._calculate_scores(app_data)

        # Identify strengths and weaknesses
        strengths = self._identify_strengths(app_data, scores)
        weaknesses = self._identify_weaknesses(app_data, scores)

        # Determine recommendation
        overall_score = scores["overall_score"]
        if overall_score >= 85:
            recommendation = "strongly_recommend"
            notes = "Exceptional candidate with strong qualifications across all areas."
        elif overall_score >= 75:
            recommendation = "recommend"
            notes = "Strong candidate who meets scholarship criteria well."
        elif overall_score >= 65:
            recommendation = "consider"
            notes = "Qualified candidate with some areas for improvement."
        else:
            recommendation = "not_recommend"
            notes = "Application has significant gaps or weaknesses."

        result = {
            "application_id": application_id,
            "analysis": {
                "academic_score": scores["academic_score"],
                "essay_score": scores["essay_score"],
                "extracurricular_score": scores["extracurricular_score"],
                "financial_need_score": scores["financial_need_score"],
                "overall_score": overall_score
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": recommendation,
            "notes": notes,
            "analysis_type": analysis_type,
            "analyzed_at": datetime.now().isoformat()
        }

        logger.info(f"Analysis complete for {application_id}: {recommendation}")
        return result

    async def _compare_applications(
        self,
        application_ids: List[str],
        comparison_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple applications side-by-side.

        Args:
            application_ids: List of application IDs to compare (2-10)
            comparison_criteria: Criteria to use for comparison

        Returns:
            Dictionary with comparison results

        Raises:
            RuntimeError: If applications cannot be loaded
        """
        logger.info(f"Comparing {len(application_ids)} applications")

        if len(application_ids) < 2:
            raise RuntimeError("At least 2 applications required for comparison")
        if len(application_ids) > 10:
            raise RuntimeError("Maximum 10 applications can be compared at once")

        # Default criteria
        if not comparison_criteria:
            comparison_criteria = ["gpa", "financial_need", "essay_quality"]

        # Analyze each application
        comparisons = []
        for app_id in application_ids:
            try:
                analysis = await self._analyze_application(app_id)
                app_data = await self.data_server._get_application(app_id)

                # Build comparison entry
                entry = {
                    "application_id": app_id,
                    "student_name": app_data.get("student_name", "Unknown"),
                    "scores": {
                        "overall": analysis["analysis"]["overall_score"],
                        "academic": analysis["analysis"]["academic_score"],
                        "essay": analysis["analysis"]["essay_score"],
                        "extracurricular": analysis["analysis"]["extracurricular_score"]
                    },
                    "recommendation": analysis["recommendation"]
                }

                comparisons.append(entry)
            except Exception as e:
                logger.error(f"Error analyzing {app_id}: {e}")
                # Continue with other applications

        # Sort by overall score
        comparisons.sort(key=lambda x: x["scores"]["overall"], reverse=True)

        # Assign ranks
        for i, comp in enumerate(comparisons, 1):
            comp["rank"] = i

        # Generate summary
        if comparisons:
            top = comparisons[0]
            summary = {
                "top_candidate": top["student_name"],
                "top_candidate_id": top["application_id"],
                "key_differences": self._identify_key_differences(comparisons),
                "recommendation": f"{top['student_name']} is the strongest candidate with an overall score of {top['scores']['overall']:.1f}"
            }
        else:
            summary = {
                "top_candidate": "None",
                "key_differences": [],
                "recommendation": "Unable to compare applications"
            }

        result = {
            "comparison": comparisons,
            "summary": summary,
            "criteria_used": comparison_criteria,
            "compared_at": datetime.now().isoformat()
        }

        logger.info(f"Comparison complete: {len(comparisons)} applications ranked")
        return result

    def _identify_key_differences(self, comparisons: List[Dict[str, Any]]) -> List[str]:
        """Identify key differences between compared applications.

        Args:
            comparisons: List of comparison entries

        Returns:
            List of key difference descriptions
        """
        differences = []

        if len(comparisons) < 2:
            return differences

        # Compare scores
        scores = [c["scores"]["overall"] for c in comparisons]
        score_range = max(scores) - min(scores)

        if score_range > 20:
            differences.append(f"Significant score variation: {score_range:.1f} points between top and bottom")

        # Compare academic scores
        academic_scores = [c["scores"]["academic"] for c in comparisons]
        if max(academic_scores) - min(academic_scores) > 30:
            differences.append("Wide range in academic qualifications")

        # Compare essay scores
        essay_scores = [c["scores"]["essay"] for c in comparisons]
        if max(essay_scores) - min(essay_scores) > 25:
            differences.append("Notable differences in personal statements and motivation")

        return differences if differences else ["Applications are relatively similar in quality"]

    async def _generate_report(
        self,
        application_ids: List[str],
        report_type: str = "summary",
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Generate a comprehensive report for applications.

        Args:
            application_ids: Application IDs to include in report
            report_type: Type of report (summary, detailed, comparison)
            include_recommendations: Whether to include recommendations

        Returns:
            Dictionary containing the generated report

        Raises:
            RuntimeError: If report cannot be generated
        """
        logger.info(f"Generating {report_type} report for {len(application_ids)} application(s)")

        report_id = str(uuid.uuid4())
        generated_at = datetime.now().isoformat()

        # Generate different report types
        if report_type == "comparison" and len(application_ids) >= 2:
            # Comparison report
            comparison = await self._compare_applications(application_ids)

            content = {
                "title": f"Application Comparison Report",
                "summary": f"Comparison of {len(application_ids)} scholarship applications",
                "applications": comparison["comparison"],
                "recommendations": []
            }

            if include_recommendations:
                content["recommendations"] = [
                    comparison["summary"]["recommendation"]
                ]

        elif report_type == "detailed":
            # Detailed report with full analysis
            applications = []
            recommendations = []

            for app_id in application_ids:
                try:
                    analysis = await self._analyze_application(app_id)
                    app_data = await self.data_server._get_application(app_id)

                    app_entry = {
                        "id": app_id,
                        "student_name": app_data.get("student_name", "Unknown"),
                        "analysis": analysis["analysis"],
                        "strengths": analysis["strengths"],
                        "weaknesses": analysis["weaknesses"],
                        "recommendation": analysis["recommendation"]
                    }

                    applications.append(app_entry)

                    if include_recommendations:
                        recommendations.append({
                            "application_id": app_id,
                            "recommendation": analysis["recommendation"],
                            "notes": analysis["notes"]
                        })
                except Exception as e:
                    logger.error(f"Error processing {app_id}: {e}")

            content = {
                "title": "Detailed Application Analysis Report",
                "summary": f"In-depth analysis of {len(applications)} application(s)",
                "applications": applications,
                "recommendations": recommendations
            }

        else:
            # Summary report (default)
            applications = []
            recommendations = []

            for app_id in application_ids:
                try:
                    app_data = await self.data_server._get_application(app_id)

                    app_entry = {
                        "id": app_id,
                        "student_name": app_data.get("student_name", "Unknown"),
                        "scholarship_name": app_data.get("scholarship_name", ""),
                        "overall_score": app_data.get("scores", {}).get("percentage", 0)
                    }

                    applications.append(app_entry)

                    if include_recommendations:
                        # Quick recommendation based on score
                        score = app_entry["overall_score"]
                        rec = "recommend" if score >= 75 else "consider"
                        recommendations.append({
                            "application_id": app_id,
                            "recommendation": rec
                        })
                except Exception as e:
                    logger.error(f"Error processing {app_id}: {e}")

            content = {
                "title": "Application Summary Report",
                "summary": f"Overview of {len(applications)} application(s)",
                "applications": applications,
                "recommendations": recommendations
            }

        result = {
            "report_id": report_id,
            "generated_at": generated_at,
            "report_type": report_type,
            "content": content,
            "download_url": f"/api/reports/{report_id}/download"
        }

        logger.info(f"Report generated: {report_id}")
        return result
