#!/usr/bin/env python3
"""
Social Presence Profile Agent for analyzing applicant social media presence.

This agent analyzes application materials to identify social media presence on
Facebook, Instagram, TikTok, and LinkedIn.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List
import ollama


class SocialAgent:
    """Agent that analyzes social media presence from application materials."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Social Agent with Ollama.
        
        Args:
            model_name: Name of the Ollama model to use
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
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
                resume_text = f"\nNote: Could not read resume: {e}\n"
        
        # Prepare essay texts
        essay_texts = ""
        if essays:
            essay_texts = "\n\nEssays:\n"
            for i, essay in enumerate(essays, 1):
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
        "social_presence_score": 0-100,
        "professional_presence_score": 0-100,
        "overall_score": 0-100
    }},
    "score_breakdown": {{
        "social_presence_score_reasoning": "Explanation of social presence score (based on number of platforms found)",
        "professional_presence_score_reasoning": "Explanation of professional presence score (emphasizing LinkedIn)",
        "overall_score_reasoning": "Explanation of overall social profile score"
    }}
}}

Return ONLY valid JSON, no additional text or markdown formatting."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.2,
                    "num_predict": 2048
                }
            )
            
            response_text = response['message']['content'].strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx + 1]
            
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response from Ollama: {str(e)}\nResponse: {response_text[:500]}")
        except Exception as e:
            raise RuntimeError(f"Error calling Ollama API: {str(e)}")

