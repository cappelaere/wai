#!/usr/bin/env python3
"""
Academic Profile Agent for analyzing applicant academic information.

This agent extracts academic information including education history, transcripts,
academic awards, relevant courses, and provides scores for academic readiness.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

from processor.agents.base_agent import BaseAgent


class AcademicAgent(BaseAgent):
    """Agent that analyzes academic information to build an academic profile."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Academic Agent with Ollama.

        Args:
            model_name: Name of the Ollama model to use
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        super().__init__(model_name=model_name, ollama_host=ollama_host, schema_name="academic_agent_schema.json")
    
    def analyze_academic_profile(
        self,
        resume: Optional[Dict],
        academic_attachments: List[Dict],
        application_profile: Dict,
        text_files_base_path: Optional[Path] = None,
        additional_criteria: Optional[str] = None
    ) -> Dict:
        """
        Analyze academic information to build an academic profile.
        
        Args:
            resume: Resume attachment with extracted text (if available)
            academic_attachments: List of academic attachment files (transcripts, grade summaries, etc.)
            application_profile: The application profile for context (contains school/program info)
            text_files_base_path: Base path where extracted text files are stored
            additional_criteria: Optional additional criteria to consider when analyzing (from academic_criteria.txt)
            
        Returns:
            Dictionary with academic profile including summary, scores, and features
        """
        # Get applicant name and basic info from application profile
        profile_data = application_profile.get('profile', {})
        applicant_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
        
        # Extract school and program info from application profile
        school_info = ""
        if profile_data:
            school_name = profile_data.get('school_name') or profile_data.get('current_school') or ""
            program = profile_data.get('program') or profile_data.get('degree_program') or ""
            if school_name or program:
                school_info = f"\nSchool/Program Information from Application:\n"
                if school_name:
                    school_info += f"  School: {school_name}\n"
                if program:
                    school_info += f"  Program: {program}\n"
        
        # Prepare resume education section
        resume_education = ""
        if resume and isinstance(resume, dict) and resume.get('extracted_text_file'):
            try:
                if text_files_base_path:
                    text_path = text_files_base_path / resume['extracted_text_file']
                else:
                    text_path = Path(resume['extracted_text_file'])
                
                if text_path.exists():
                    with open(text_path, 'r', encoding='utf-8') as f:
                        resume_text = f.read()
                        # Try to extract education section (look for common headers)
                        resume_education = f"\nResume (Education Section):\n{resume_text[:5000]}\n"
            except Exception as e:
                resume_education = f"\nNote: Could not read resume: {e}\n"
        
        # Prepare academic attachment texts (transcripts, grade summaries, etc.)
        academic_texts = ""
        if academic_attachments:
            academic_texts = "\n\nAcademic Documents (Transcripts, Grade Summaries, etc.):\n"
            for i, attachment in enumerate(academic_attachments, 1):
                if attachment.get('extracted_text_file'):
                    try:
                        if text_files_base_path:
                            text_path = text_files_base_path / attachment['extracted_text_file']
                        else:
                            text_path = Path(attachment['extracted_text_file'])
                        
                        if text_path.exists():
                            with open(text_path, 'r', encoding='utf-8') as f:
                                attachment_text = f.read()
                                academic_texts += f"\nDocument {i} ({attachment.get('filename', 'unknown')}):\n{attachment_text[:3000]}\n"
                    except Exception as e:
                        academic_texts += f"\nDocument {i} ({attachment.get('filename', 'unknown')}): Error reading file: {e}\n"
        else:
            academic_texts = "\n\nNo academic documents (transcripts, grade summaries) provided."
        
        # Add additional criteria section if provided
        criteria_section = ""
        if additional_criteria:
            criteria_section = f"""

Additional Scholarship-Specific Criteria:
{additional_criteria}

Please take these additional criteria into account when analyzing the academic profile and scoring.
"""
        
        prompt = f"""You are an Academic Profile Agent analyzing academic information for a WAI (Women in Aviation International) scholarship applicant.

Applicant: {applicant_name if applicant_name else "Unknown"}
{school_info}

Your task is to analyze the academic information to extract:
1. Current school name and program of study
2. Education level (high school, undergraduate, graduate, etc.)
3. Academic performance indicators (GPA, grades, honors, etc.)
4. Academic awards and achievements
5. Relevant courses related to aviation, STEM, or the scholarship focus
6. Academic trajectory and progression
7. Academic readiness for the scholarship and aviation career goals

{resume_education}{academic_texts}{criteria_section}

Based on the academic information provided{', and the additional criteria provided above' if additional_criteria else ''}, provide a JSON response with the following structure:

{{
    "summary": "A 1 paragraph summary (4-6 sentences) of the applicant's academic trajectory, performance, and readiness for aviation studies",
    "profile_features": {{
        "current_school_name": "name of current school or institution",
        "program": "program of study or major",
        "education_level": "high_school|undergraduate|graduate|other",
        "academic_performance": {{
            "gpa": "GPA if mentioned, or null",
            "gpa_scale": "4.0|other|null",
            "academic_standing": "excellent|good|satisfactory|other",
            "performance_notes": "any notes about academic performance"
        }},
        "academic_awards": ["list of academic awards, honors, or recognitions"],
        "relevant_courses": ["list of relevant courses related to aviation, STEM, or scholarship focus"],
        "academic_trajectory": "description of academic progression and trajectory",
        "strengths": ["key academic strengths identified"],
        "areas_for_improvement": ["any areas for improvement noted, or empty array if none"]
    }},
    "scores": {{
        "academic_performance_score": <integer 0-100, required>,
        "academic_relevance_score": <integer 0-100, required>,
        "academic_readiness_score": <integer 0-100, required>,
        "overall_score": <integer 0-100, required>
    }},
    "score_breakdown": {{
        "academic_performance_score_reasoning": "Explanation of academic performance score",
        "academic_relevance_score_reasoning": "Explanation of how relevant the academic background is to aviation/scholarship",
        "academic_readiness_score_reasoning": "Explanation of academic readiness for scholarship and aviation career goals"
    }}
}}

CRITICAL JSON FORMAT REQUIREMENTS:
- You MUST respond with ONLY valid JSON
- Do NOT include markdown code blocks (```json or ```)
- Do NOT include any text before or after the JSON
- Do NOT include comments or explanations
- Do NOT use trailing commas
- Do NOT use single quotes (use double quotes only)
- All scores must be integers between 0 and 100
- The response must be parseable by json.loads() without any preprocessing"""

        try:
            # Build full file path for debugging (use absolute paths)
            full_filename = "unknown"
            if resume and isinstance(resume, dict) and text_files_base_path and resume.get('extracted_text_file'):
                file_path = text_files_base_path / resume['extracted_text_file']
                full_filename = str(file_path.resolve() if hasattr(file_path, 'resolve') else file_path.absolute())
            elif resume and isinstance(resume, dict) and resume.get('filename'):
                full_filename = resume.get('filename')

            # Prepare messages for potential retry
            messages = [{"role": "user", "content": prompt}]

            response_text = self._chat_with_retry(messages, system_message=self.system_message)

            # Use BaseAgent's JSON parsing method (handles markdown extraction and retry)
            result = self.parse_llm_response(response_text, filename=full_filename, messages=messages)
            return result

        except ValueError as e:
            raise RuntimeError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error analyzing academic profile: {str(e)}")

