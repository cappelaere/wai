#!/usr/bin/env python3
"""
Recommendation Profile Agent for analyzing recommendation letters.

This agent extracts information from recommendation letters including recommender details,
key strengths mentioned, and provides scores for recommendation strength and consistency.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

from processor.agents.base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    """Agent that analyzes recommendation letters to build a recommendation profile."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Recommendation Agent with Ollama.

        Args:
            model_name: Name of the Ollama model to use
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        super().__init__(model_name=model_name, ollama_host=ollama_host, schema_name="recommendation_agent_schema.json")
    
    def analyze_recommendation_profile(
        self,
        recommendations: List[Dict],
        application_profile: Dict,
        text_files_base_path: Optional[Path] = None,
        additional_criteria: Optional[str] = None
    ) -> Dict:
        """
        Analyze recommendation letters to build a recommendation profile.
        
        Args:
            recommendations: List of recommendation letter attachments with extracted text
            application_profile: The application profile for context
            text_files_base_path: Base path where extracted text files are stored
            additional_criteria: Optional additional criteria to consider when analyzing
            
        Returns:
            Dictionary with recommendation profile including summary, scores, and features
        """
        # Prepare recommendation texts
        recommendation_texts = []
        # Ensure recommendations is a list
        if not isinstance(recommendations, list):
            recommendations = [recommendations] if recommendations else []

        for rec in recommendations:
            # Ensure rec is a dict before calling .get()
            if not isinstance(rec, dict):
                continue
            if rec.get('extracted_text_file'):
                # Read the extracted text file
                try:
                    if text_files_base_path:
                        text_path = text_files_base_path / rec['extracted_text_file']
                    else:
                        text_path = Path(rec['extracted_text_file'])
                    
                    if text_path.exists():
                        with open(text_path, 'r', encoding='utf-8') as f:
                            recommendation_texts.append({
                                "filename": rec['filename'],
                                "text": f.read()
                            })
                except Exception as e:
                    print(f"Warning: Could not read recommendation text from {rec['extracted_text_file']}: {e}")
        
        # Get applicant name from application profile for context
        profile_data = application_profile.get('profile', {})
        applicant_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
        
        # Build prompt
        recommendations_section = ""
        if recommendation_texts:
            recommendations_section = "\n\nRecommendation Letters:\n"
            for i, rec in enumerate(recommendation_texts, 1):
                recommendations_section += f"\nRecommendation Letter {i} ({rec['filename']}):\n{rec['text'][:3000]}\n"
        else:
            recommendations_section = "\n\nNo recommendation letters found."
        
        # Add additional criteria section if provided
        criteria_section = ""
        if additional_criteria:
            criteria_section = f"""

Additional Scholarship-Specific Criteria:
{additional_criteria}

Please take these additional criteria into account when analyzing the recommendations and scoring.
"""
        
        prompt = f"""You are a Recommendation Profile Agent analyzing recommendation letters for a WAI (Women in Aviation International) scholarship applicant.

Applicant: {applicant_name if applicant_name else "Unknown"}

Your task is to analyze the recommendation letters to extract:
1. Recommender information (role, relationship to applicant, duration of relationship)
2. Key strengths and positive attributes mentioned
3. Specific examples or evidence provided
4. Potential concerns or areas for improvement (if any)
5. Overall strength and depth of support
6. Consistency across multiple recommendations (if applicable)

{recommendations_section}{criteria_section}

Based on the recommendation letters{', and the additional criteria provided above' if additional_criteria else ''}, provide a JSON response with the following structure:

{{
    "summary": "A 1 paragraph summary (4-6 sentences) of the overall recommendation strength, key themes, and consistency across letters",
    "profile_features": {{
        "recommendations": [
            {{
                "recommender_role": "instructor|employer|mentor|colleague|other",
                "relationship_duration": "description of how long they've known the applicant",
                "key_strengths_mentioned": ["list of key strengths or positive attributes"],
                "specific_examples": ["specific examples or evidence provided"],
                "potential_concerns": ["any concerns or areas for improvement mentioned, or empty array if none"],
                "overall_tone": "very_positive|positive|neutral|mixed"
            }}
        ],
        "aggregate_analysis": {{
            "common_themes": ["themes that appear across multiple letters"],
            "strength_consistency": "high|medium|low",
            "depth_of_support": "deep|moderate|surface_level"
        }}
    }},
    "scores": {{
        "average_support_strength_score": <integer 0-100, required>,
        "consistency_of_support_score": <integer 0-100, required>,
        "depth_of_endorsement_score": <integer 0-100, required>,
        "overall_score": <integer 0-100, required>
    }},
    "score_breakdown": {{
        "average_support_strength_score_reasoning": "Explanation of average support strength score",
        "consistency_of_support_score_reasoning": "Explanation of consistency score",
        "depth_of_endorsement_score_reasoning": "Explanation of depth of endorsement score"
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
            if recommendations:
                for rec in recommendations:
                    if isinstance(rec, dict):
                        if text_files_base_path and rec.get('extracted_text_file'):
                            file_path = text_files_base_path / rec['extracted_text_file']
                            file_paths.append(str(file_path.resolve() if hasattr(file_path, 'resolve') else file_path.absolute()))
                        elif rec.get('filename'):
                            file_paths.append(rec.get('filename'))

            full_filename = " | ".join(file_paths) if file_paths else "unknown"

            # Prepare messages for potential retry
            messages = [{"role": "user", "content": prompt}]

            response_text = self._chat_with_retry(messages, system_message=self.system_message)

            # Use BaseAgent's JSON parsing method (handles markdown extraction and retry)
            result = self.parse_llm_response(response_text, filename=full_filename, messages=messages)
            return result

        except ValueError as e:
            raise RuntimeError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error analyzing recommendation profile: {str(e)}")

