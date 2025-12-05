#!/usr/bin/env python3
"""
Application Profile Agent for analyzing WAI scholarship application forms.

This agent extracts structured information from application forms, assesses completeness,
and generates application profiles with scores.
"""

import json
from typing import Optional, Dict, List

from processor.agents.base_agent import BaseAgent


class ApplicationAgent(BaseAgent):
    """Agent that analyzes application forms and generates profiles using Ollama."""

    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Application Agent with Ollama.

        Args:
            model_name: Name of the Ollama model to use (e.g., "llama3.2", "mistral", "phi3")
                       Default: "llama3.2"
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        super().__init__(model_name=model_name, ollama_host=ollama_host, schema_name="application_agent_schema.json")
    
    def analyze_application(self, extracted_text: str, file_list: List[str], additional_criteria: Optional[str] = None) -> Dict:
        """
        Analyze the application form text and generate a profile.
        
        Args:
            extracted_text: Text extracted from the application form
            file_list: List of all files in the application folder
            additional_criteria: Optional additional criteria to consider when analyzing (from application_criteria.txt)
            
        Returns:
            Dictionary with profile, summary, and score
        """
        # Count attachments
        num_attachments = len([f for f in file_list if '_' in f and f.split('_')[-1].split('.')[0].isdigit()])
        
        # Add additional criteria section if provided
        criteria_section = ""
        if additional_criteria:
            criteria_section = f"""

Additional Scholarship-Specific Criteria:
{additional_criteria}

Please take these additional criteria into account when analyzing the application, assessing completeness, and scoring.
"""
        
        prompt = f"""You are an Application Agent analyzing a WAI (Women in Aviation International) scholarship application form.

Your task is to:
1. Extract structured information from the application form
2. Assess completeness based on what information is present or missing
3. Generate a summary of the application
4. Provide an overall score (0-100) that evaluates the overall quality and completeness of the application{', considering the additional criteria provided above' if additional_criteria else ''}
5. Also provide a completeness score (0-100) specifically measuring how much required information was provided

Application Form Text:
{extracted_text}

Files in Application Folder:
{json.dumps(file_list, indent=2)}{criteria_section}

Based on the application form text and the list of files{', and the additional criteria provided above' if additional_criteria else ''}, please provide a JSON response with the following structure:

{{
    "profile": {{
        "wai_membership_number": "extracted or null",
        "wai_application_number": "extracted or null",
        "first_name": "extracted or null",
        "middle_name": "extracted or null",
        "last_name": "extracted or null",
        "email": "extracted or null",
        "membership_since": "extracted or null",
        "membership_expiration": "extracted or null",
        "home_address": {{
            "country": "extracted or null",
            "address_1": "extracted or null",
            "address_2": "extracted or null",
            "city": "extracted or null",
            "state_province": "extracted or null",
            "zip_postal_code": "extracted or null",
            "home_phone": "extracted or null",
            "work_phone": "extracted or null"
        }},
        "school_information": {{
            "country": "extracted or null",
            "school_name": "extracted or null",
            "address_1": "extracted or null",
            "address_2": "extracted or null",
            "city": "extracted or null",
            "state_province": "extracted or null",
            "zip_postal_code": "extracted or null"
        }},
        "completeness": {{
            "has_resume": true/false,
            "has_essay": true/false,
            "num_recommendation_letters": 0-3,
            "has_medical_certificate": true/false,
            "has_logbook": true/false,
            "num_attachments": {num_attachments}
        }}
    }},
    "summary": "A 2-3 sentence summary of who this applicant is and what is in their application package",
    "scores": {{
        "overall_score": <integer 0-100, required>,
        "completeness_score": <integer 0-100, required>,
        "score_breakdown": {{
            "profile_information": "score and reasoning",
            "contact_information": "score and reasoning",
            "school_information": "score and reasoning",
            "supporting_documents": "score and reasoning"
        }},
        "missing_items": ["list of missing or incomplete items"]
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
            # Prepare messages for potential retry
            messages = [{"role": "user", "content": prompt}]

            # Use BaseAgent's retry-enabled chat method with system message
            response_text = self._chat_with_retry(messages, system_message=self.system_message)

            # Use BaseAgent's JSON parsing method (handles markdown extraction and retry)
            result = self.parse_llm_response(response_text, filename="application_form", messages=messages)
            return result

        except ValueError as e:
            raise RuntimeError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error analyzing application: {str(e)}")

