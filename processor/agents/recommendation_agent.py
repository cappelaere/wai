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
        super().__init__(model_name=model_name, ollama_host=ollama_host)
    
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
        for rec in recommendations:
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
        "average_support_strength_score": 0-100,
        "consistency_of_support_score": 0-100,
        "depth_of_endorsement_score": 0-100,
        "overall_score": 0-100
    }},
    "score_breakdown": {{
        "average_support_strength_score_reasoning": "Explanation of average support strength score",
        "consistency_of_support_score_reasoning": "Explanation of consistency score",
        "depth_of_endorsement_score_reasoning": "Explanation of depth of endorsement score"
    }}
}}

Return ONLY valid JSON, no additional text or markdown formatting."""

        try:
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
            raise RuntimeError(f"Error analyzing recommendation profile: {str(e)}")

