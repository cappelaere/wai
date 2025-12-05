#!/usr/bin/env python3
"""
Social Presence Profile Agent for analyzing applicant social media presence.

This agent analyzes application materials to identify social media presence on
Facebook, Instagram, TikTok, and LinkedIn.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

from processor.agents.base_agent import BaseAgent


class SocialAgent(BaseAgent):
    """Agent that analyzes social media presence from application materials."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Social Agent with Ollama.

        Args:
            model_name: Name of the Ollama model to use
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        super().__init__(model_name=model_name, ollama_host=ollama_host, schema_name="social_agent_schema.json")
    
    def analyze_social_presence(
        self,
        resume: Optional[Dict],
        essays: List[Dict],
        application_profile: Dict,
        text_files_base_path: Optional[Path] = None,
        additional_criteria: Optional[str] = None
    ) -> Dict:
        """
        Analyze application materials to identify social media presence.
        
        Args:
            resume: Resume attachment with extracted text (if available)
            essays: List of essay attachments with extracted text
            application_profile: The application profile for context
            text_files_base_path: Base path where extracted text files are stored
            additional_criteria: Optional additional criteria to consider when analyzing
            
        Returns:
            Dictionary with social presence profile including platforms found and links
        """
        # Get applicant name from application profile for context
        profile_data = application_profile.get('profile', {})
        applicant_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
        
        # Prepare resume text
        resume_text = ""
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
                resume_text = f"\nNote: Could not read resume: {e}\n"
        
        # Prepare essay texts
        essay_texts = ""
        # Ensure essays is a list
        if not isinstance(essays, list):
            essays = [essays] if essays else []

        if essays:
            essay_texts = "\n\nEssays:\n"
            for i, essay in enumerate(essays, 1):
                # Ensure essay is a dict before calling .get()
                if not isinstance(essay, dict):
                    continue
                if essay.get('extracted_text_file'):
                    try:
                        if text_files_base_path:
                            text_path = text_files_base_path / essay['extracted_text_file']
                        else:
                            text_path = Path(essay['extracted_text_file'])
                        
                        if text_path.exists():
                            with open(text_path, 'r', encoding='utf-8') as f:
                                essay_text = f.read()
                                essay_texts += f"\nEssay {i} ({essay.get('filename', 'unknown')}):\n{essay_text[:2000]}\n"
                    except Exception as e:
                        essay_texts += f"\nEssay {i}: Error reading file: {e}\n"
        else:
            essay_texts = "\n\nNo essays found."
        
        # Get email and other contact info from application profile
        contact_info = ""
        if profile_data:
            email = profile_data.get('email', '')
            if email:
                contact_info = f"\nContact Information:\n  Email: {email}\n"
        
        # Add additional criteria section if provided
        criteria_section = ""
        if additional_criteria:
            criteria_section = f"""

Additional Scholarship-Specific Criteria:
{additional_criteria}

Please take these additional criteria into account when analyzing social media presence.
"""
        
        prompt = f"""You are a Social Presence Agent analyzing a WAI (Women in Aviation International) scholarship applicant's social media presence.

Applicant: {applicant_name if applicant_name else "Unknown"}
{contact_info}

Your task is to analyze the application materials (resume, essays, application form) to identify:
1. Social media links or mentions for Facebook, Instagram, TikTok, and LinkedIn
2. Professional social media presence (especially LinkedIn)
3. Any social media handles, usernames, or profile links mentioned
4. Evidence of social media activity or engagement

Look for:
- Direct links (e.g., linkedin.com/in/username, facebook.com/username, instagram.com/username, tiktok.com/@username)
- Mentions of social media platforms
- Social media handles or usernames
- References to social media activity or content

Resume:
{resume_text[:3000] if resume_text else "No resume found."}
{essay_texts}{criteria_section}

Based on the application materials{', and the additional criteria provided above' if additional_criteria else ''}, provide a JSON response with the following structure:

{{
    "summary": "A brief summary (2-3 sentences) of the applicant's social media presence found in the application materials",
    "profile_features": {{
        "platforms_found": {{
            "facebook": {{
                "present": true/false,
                "link": "full URL if found, or null",
                "handle": "username/handle if found, or null",
                "evidence": "description of where it was found"
            }},
            "instagram": {{
                "present": true/false,
                "link": "full URL if found, or null",
                "handle": "username/handle if found, or null",
                "evidence": "description of where it was found"
            }},
            "tiktok": {{
                "present": true/false,
                "link": "full URL if found, or null",
                "handle": "username/handle if found, or null",
                "evidence": "description of where it was found"
            }},
            "linkedin": {{
                "present": true/false,
                "link": "full URL if found, or null",
                "handle": "username/handle if found, or null",
                "evidence": "description of where it was found"
            }}
        }},
        "total_platforms": 0-4,
        "has_professional_presence": true/false,
        "notes": "any additional notes about social media presence or lack thereof"
    }},
    "scores": {{
        "social_presence_score": <integer 0-100, required>,
        "professional_presence_score": <integer 0-100, required>,
        "overall_score": <integer 0-100, required>
    }},
    "score_breakdown": {{
        "social_presence_score_reasoning": "Explanation of social presence score (based on number of platforms found)",
        "professional_presence_score_reasoning": "Explanation of professional presence score (emphasizing LinkedIn)",
        "overall_score_reasoning": "Explanation of overall social profile score"
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

            response_text = self._chat_with_retry(messages, system_message=self.system_message)

            # Use BaseAgent's JSON parsing method (handles markdown extraction and retry)
            result = self.parse_llm_response(response_text, filename=full_filename, messages=messages)
            return result

        except ValueError as e:
            raise RuntimeError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error analyzing social presence: {str(e)}")

