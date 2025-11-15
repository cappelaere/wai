#!/usr/bin/env python3
"""
Application Profile Agent for analyzing WAI scholarship application forms.

This agent extracts structured information from application forms, assesses completeness,
and generates application profiles with scores.
"""

import os
import json
from typing import Optional, Dict, List
import ollama


class ApplicationAgent:
    """Agent that analyzes application forms and generates profiles using Ollama."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Application Agent with Ollama.
        
        Args:
            model_name: Name of the Ollama model to use (e.g., "llama3.2", "mistral", "phi3")
                       Default: "llama3.2"
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Test connection to Ollama
        try:
            # Check if Ollama is running and model is available
            models_response = ollama.list()
            # ollama.list() returns a ListResponse object with a 'models' attribute
            # Each model is a Model object with a 'model' attribute containing the name
            model_list = models_response.models if hasattr(models_response, 'models') else []
            model_names = [m.model for m in model_list if hasattr(m, 'model')]
            if model_name not in model_names:
                print(f"Warning: Model '{model_name}' not found locally.")
                print(f"Available models: {', '.join(model_names) if model_names else 'None'}")
                print(f"To download the model, run: ollama pull {model_name}")
                print(f"Attempting to use '{model_name}' anyway (it will be downloaded if needed)...")
        except Exception as e:
            print(f"Warning: Could not connect to Ollama at {self.ollama_host}")
            print(f"Error: {str(e)}")
            print("Make sure Ollama is running. Start it with: ollama serve")
            print("Or install Ollama from: https://ollama.com/download")
            raise RuntimeError(f"Cannot connect to Ollama: {str(e)}")
    
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
        "overall_score": 0-100,
        "completeness_score": 0-100,
        "score_breakdown": {{
            "profile_information": "score and reasoning",
            "contact_information": "score and reasoning",
            "school_information": "score and reasoning",
            "supporting_documents": "score and reasoning"
        }},
        "missing_items": ["list of missing or incomplete items"]
    }}
}}

Return ONLY valid JSON, no additional text or markdown formatting."""

        try:
            # Call Ollama API
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.1,  # Lower temperature for more consistent JSON output
                    "num_predict": 4096  # Maximum tokens to generate
                }
            )
            
            # Extract JSON from response
            response_text = response['message']['content'].strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Try to extract JSON if it's embedded in text
            # Look for JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx + 1]
            
            # Parse JSON
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response from Ollama: {str(e)}\nResponse: {response_text[:500]}")
        except Exception as e:
            raise RuntimeError(f"Error calling Ollama API: {str(e)}")

