#!/usr/bin/env python3
"""
Personal Profile Agent for analyzing applicant essays and resumes.

This agent extracts personal information including motivation, career goals,
community service, leadership, and character indicators from essays and resumes.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

from processor.agents.base_agent import BaseAgent


class PersonalAgent(BaseAgent):
    """Agent that analyzes personal information from essays and resumes to build a personal profile."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Personal Agent with Ollama.

        Args:
            model_name: Name of the Ollama model to use
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        super().__init__(model_name=model_name, ollama_host=ollama_host, schema_name="personal_agent_schema.json")
    
    def analyze_personal_profile(
        self, 
        essays: List[Dict], 
        resume: Optional[Dict],
        application_profile: Dict,
        text_files_base_path: Optional[Path] = None,
        additional_criteria: Optional[str] = None
    ) -> Dict:
        """
        Analyze personal information from essays and resume to build a personal profile.
        
        Args:
            essays: List of essay attachments with extracted text
            resume: Resume attachment with extracted text (if available)
            application_profile: The application profile for context
            text_files_base_path: Base path where extracted text files are stored
            additional_criteria: Optional additional criteria to consider when analyzing (from personal_criteria.txt)
            
        Returns:
            Dictionary with personal profile including summary, scores, and features
        """
        # Prepare essay texts
        essay_texts = []
        # Ensure essays is a list
        if not isinstance(essays, list):
            essays = [essays] if essays else []

        for essay in essays:
            # Ensure essay is a dict before calling .get()
            if not isinstance(essay, dict):
                continue
            if essay.get('extracted_text_file'):
                # Read the extracted text file
                try:
                    if text_files_base_path:
                        text_path = text_files_base_path / essay['extracted_text_file']
                    else:
                        text_path = Path(essay['extracted_text_file'])
                    
                    if text_path.exists():
                        with open(text_path, 'r', encoding='utf-8') as f:
                            essay_texts.append({
                                "filename": essay['filename'],
                                "text": f.read()
                            })
                except Exception as e:
                    print(f"Warning: Could not read essay text from {essay['extracted_text_file']}: {e}")
        
        # Prepare resume text
        resume_text = ""
        # Ensure resume is a dict before calling .get()
        if resume and isinstance(resume, dict) and resume.get('extracted_text_file'):
            try:
                if text_files_base_path:
                    text_path = text_files_base_path / resume['extracted_text_file']
                else:
                    text_path = Path(resume['extracted_text_file'])
                
                if text_path.exists():
                    with open(text_path, 'r', encoding='utf-8') as f:
                        resume_text = f.read()
            except Exception as e:
                print(f"Warning: Could not read resume text from {resume['extracted_text_file']}: {e}")
        
        # Get applicant name from application profile for context
        profile_data = application_profile.get('profile', {})
        applicant_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
        
        # Build prompt
        essays_section = ""
        if essay_texts:
            essays_section = "\n\nEssays:\n"
            for i, essay in enumerate(essay_texts, 1):
                essays_section += f"\nEssay {i} ({essay['filename']}):\n{essay['text'][:3000]}\n"
        else:
            essays_section = "\n\nNo essays found."
        
        resume_section = f"\n\nResume:\n{resume_text[:3000]}" if resume_text else "\n\nNo resume found."
        
        # Add additional criteria section if provided
        criteria_section = ""
        if additional_criteria:
            criteria_section = f"""

Additional Scholarship-Specific Criteria:
{additional_criteria}

Please take these additional criteria into account when analyzing the applicant and scoring their personal profile.
"""
        
        prompt = f"""You are a Personal Profile Agent analyzing a WAI (Women in Aviation International) scholarship applicant's personal information.

Applicant: {applicant_name if applicant_name else "Unknown"}

Your task is to analyze the applicant's essays and resume to extract:
1. Motivation and passion for aviation
2. Career goals and clarity
3. Community service involvement
4. Leadership roles and experiences
5. Personal character indicators (persistence, teamwork, etc.)
6. Aviation path stage (exploring/training/early-career/professional)

{essays_section}
{resume_section}{criteria_section}

Based on the essays and resume{', and the additional criteria provided above' if additional_criteria else ''}, provide a JSON response with the following structure:

{{
    "summary": "A 1 paragraph summary (4-6 sentences) of the applicant's personal story, passion, and alignment with WAI and aviation",
    "profile_features": {{
        "motivation_summary": "Summary of the applicant's motivation and passion for aviation",
        "career_goals_summary": "Summary of the applicant's career goals and aspirations",
        "aviation_path_stage": "exploring|training|early-career|professional",
        "community_service_summary": "Summary of community service involvement or null if not mentioned",
        "leadership_roles": ["list of leadership roles or positions mentioned"],
        "personal_character_indicators": ["tags like persistence, teamwork, dedication, etc."]
    }},
    "scores": {{
        "motivation_score": <integer 0-100, required>,
        "goals_clarity_score": <integer 0-100, required>,
        "character_service_leadership_score": <integer 0-100, required>,
        "overall_score": <integer 0-100, required>
    }},
    "score_breakdown": {{
        "motivation_score_reasoning": "Explanation of motivation score",
        "goals_clarity_score_reasoning": "Explanation of goals clarity score",
        "character_service_leadership_score_reasoning": "Explanation of character/service/leadership score"
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
            file_paths = []
            if essays:
                for essay in essays:
                    if isinstance(essay, dict) and text_files_base_path and essay.get('extracted_text_file'):
                        file_path = text_files_base_path / essay['extracted_text_file']
                        file_paths.append(str(file_path.resolve() if hasattr(file_path, 'resolve') else file_path.absolute()))
            if resume and isinstance(resume, dict) and text_files_base_path and resume.get('extracted_text_file'):
                file_path = text_files_base_path / resume['extracted_text_file']
                file_paths.append(str(file_path.resolve() if hasattr(file_path, 'resolve') else file_path.absolute()))

            full_filename = " | ".join(file_paths) if file_paths else (applicant_name if applicant_name else "unknown")

            # Prepare messages for potential retry
            messages = [{"role": "user", "content": prompt}]

            # Use BaseAgent's retry-enabled chat method with system message
            response_text = self._chat_with_retry(messages, system_message=self.system_message)

            # Use BaseAgent's JSON parsing method (handles markdown extraction and retry)
            result = self.parse_llm_response(response_text, filename=full_filename, messages=messages)
            return result

        except ValueError as e:
            raise RuntimeError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error analyzing personal profile: {str(e)}")

