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
        super().__init__(model_name=model_name, ollama_host=ollama_host)
    
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
        for essay in essays:
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
        if resume and resume.get('extracted_text_file'):
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
        "motivation_score": 0-100,
        "goals_clarity_score": 0-100,
        "character_service_leadership_score": 0-100,
        "overall_score": 0-100
    }},
    "score_breakdown": {{
        "motivation_score_reasoning": "Explanation of motivation score",
        "goals_clarity_score_reasoning": "Explanation of goals clarity score",
        "character_service_leadership_score_reasoning": "Explanation of character/service/leadership score"
    }}
}}

Return ONLY valid JSON, no additional text or markdown formatting."""

        try:
            # Use BaseAgent's retry-enabled chat method
            response_text = self._chat_with_retry(
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx + 1]

            # Use BaseAgent's JSON parsing method
            result = self.parse_llm_response(response_text)
            return result

        except ValueError as e:
            raise RuntimeError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error analyzing personal profile: {str(e)}")

