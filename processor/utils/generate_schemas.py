#!/usr/bin/env python3
"""
Generate JSON schemas for all agent outputs.

This script creates JSON Schema files for:
- ApplicationAgent
- PersonalAgent
- RecommendationAgent
- AcademicAgent
- SocialAgent
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_schema_dir() -> Path:
    """Get the schema directory from environment variable or use default."""
    schema_dir = os.getenv("SCHEMA_OUTPUT_DIR", "schemas")
    return Path(schema_dir)


def create_application_agent_schema() -> Dict[str, Any]:
    """Create JSON schema for ApplicationAgent output."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Application Agent Output Schema",
        "description": "Schema for ApplicationAgent output structure",
        "type": "object",
        "properties": {
            "profile": {
                "type": "object",
                "properties": {
                    "wai_membership_number": {"type": ["string", "null"]},
                    "wai_application_number": {"type": ["string", "null"]},
                    "first_name": {"type": ["string", "null"]},
                    "middle_name": {"type": ["string", "null"]},
                    "last_name": {"type": ["string", "null"]},
                    "email": {"type": ["string", "null"]},
                    "membership_since": {"type": ["string", "null"]},
                    "membership_expiration": {"type": ["string", "null"]},
                    "home_address": {
                        "type": "object",
                        "properties": {
                            "country": {"type": ["string", "null"]},
                            "address_1": {"type": ["string", "null"]},
                            "address_2": {"type": ["string", "null"]},
                            "city": {"type": ["string", "null"]},
                            "state_province": {"type": ["string", "null"]},
                            "zip_postal_code": {"type": ["string", "null"]},
                            "home_phone": {"type": ["string", "null"]},
                            "work_phone": {"type": ["string", "null"]}
                        }
                    },
                    "school_information": {
                        "type": "object",
                        "properties": {
                            "country": {"type": ["string", "null"]},
                            "school_name": {"type": ["string", "null"]},
                            "address_1": {"type": ["string", "null"]},
                            "address_2": {"type": ["string", "null"]},
                            "city": {"type": ["string", "null"]},
                            "state_province": {"type": ["string", "null"]},
                            "zip_postal_code": {"type": ["string", "null"]}
                        }
                    },
                    "completeness": {
                        "type": "object",
                        "properties": {
                            "has_resume": {"type": "boolean"},
                            "has_essay": {"type": "boolean"},
                            "num_recommendation_letters": {"type": "integer"},
                            "has_medical_certificate": {"type": "boolean"},
                            "has_logbook": {"type": "boolean"},
                            "num_attachments": {"type": "integer"}
                        }
                    }
                },
                "required": []
            },
            "summary": {"type": "string"},
            "scores": {
                "type": "object",
                "properties": {
                    "overall_score": {"type": ["integer", "number"]},
                    "completeness_score": {"type": ["integer", "number"]},
                    "score_breakdown": {
                        "type": "object",
                        "properties": {
                            "profile_information": {"type": ["string", "number"]},
                            "contact_information": {"type": ["string", "number"]},
                            "school_information": {"type": ["string", "number"]},
                            "supporting_documents": {"type": ["string", "number"]}
                        }
                    },
                    "missing_items": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["overall_score", "completeness_score"]
            }
        },
        "required": ["profile", "summary", "scores"]
    }


def create_personal_agent_schema() -> Dict[str, Any]:
    """Create JSON schema for PersonalAgent output."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Personal Agent Output Schema",
        "description": "Schema for PersonalAgent output structure",
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "profile_features": {
                "type": "object",
                "properties": {
                    "motivation_summary": {"type": "string"},
                    "career_goals_summary": {"type": "string"},
                    "aviation_path_stage": {
                        "type": "string",
                        "enum": ["exploring", "training", "early_career", "professional", "other"]
                    },
                    "community_service_summary": {"type": "string"},
                    "leadership_roles": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "personal_character_indicators": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "alignment_with_wai": {"type": "string"},
                    "unique_strengths": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "scores": {
                "type": "object",
                "properties": {
                    "motivation_score": {"type": ["integer", "number"]},
                    "goals_clarity_score": {"type": ["integer", "number"]},
                    "character_service_leadership_score": {"type": ["integer", "number"]},
                    "overall_score": {"type": ["integer", "number"]}
                },
                "required": ["overall_score"]
            },
            "score_breakdown": {
                "type": "object",
                "properties": {
                    "motivation_score_reasoning": {"type": "string"},
                    "goals_clarity_score_reasoning": {"type": "string"},
                    "character_service_leadership_score_reasoning": {"type": "string"},
                    "overall_score_reasoning": {"type": "string"}
                }
            }
        },
        "required": ["summary", "profile_features", "scores"]
    }


def create_recommendation_agent_schema() -> Dict[str, Any]:
    """Create JSON schema for RecommendationAgent output."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Recommendation Agent Output Schema",
        "description": "Schema for RecommendationAgent output structure",
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "profile_features": {
                "type": "object",
                "properties": {
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "recommender_role": {
                                    "type": "string",
                                    "enum": ["instructor", "employer", "mentor", "colleague", "other"]
                                },
                                "relationship_duration": {"type": "string"},
                                "key_strengths_mentioned": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "specific_examples": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "potential_concerns": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "overall_tone": {
                                    "type": "string",
                                    "enum": ["very_positive", "positive", "neutral", "mixed"]
                                }
                            }
                        }
                    },
                    "aggregate_analysis": {
                        "type": "object",
                        "properties": {
                            "common_themes": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "strength_consistency": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            },
                            "depth_of_support": {
                                "type": "string",
                                "enum": ["deep", "moderate", "surface_level"]
                            }
                        }
                    }
                }
            },
            "scores": {
                "type": "object",
                "properties": {
                    "average_support_strength_score": {"type": ["integer", "number"]},
                    "consistency_of_support_score": {"type": ["integer", "number"]},
                    "depth_of_endorsement_score": {"type": ["integer", "number"]},
                    "overall_score": {"type": ["integer", "number"]}
                },
                "required": ["overall_score"]
            },
            "score_breakdown": {
                "type": "object",
                "properties": {
                    "average_support_strength_score_reasoning": {"type": "string"},
                    "consistency_of_support_score_reasoning": {"type": "string"},
                    "depth_of_endorsement_score_reasoning": {"type": "string"}
                }
            }
        },
        "required": ["summary", "profile_features", "scores"]
    }


def create_academic_agent_schema() -> Dict[str, Any]:
    """Create JSON schema for AcademicAgent output."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Academic Agent Output Schema",
        "description": "Schema for AcademicAgent output structure",
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "profile_features": {
                "type": "object",
                "properties": {
                    "current_school_name": {"type": ["string", "null"]},
                    "program": {"type": ["string", "null"]},
                    "education_level": {
                        "type": ["string", "null"],
                        "enum": ["high_school", "undergraduate", "graduate", "other", None]
                    },
                    "gpa": {"type": ["string", "null"]},
                    "academic_awards": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "relevant_courses": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "academic_trajectory": {"type": "string"},
                    "strengths": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "areas_for_improvement": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "scores": {
                "type": "object",
                "properties": {
                    "academic_performance_score": {"type": ["integer", "number"]},
                    "academic_relevance_score": {"type": ["integer", "number"]},
                    "academic_readiness_score": {"type": ["integer", "number"]},
                    "overall_score": {"type": ["integer", "number"]}
                },
                "required": ["overall_score"]
            },
            "score_breakdown": {
                "type": "object",
                "properties": {
                    "academic_performance_score_reasoning": {"type": "string"},
                    "academic_relevance_score_reasoning": {"type": "string"},
                    "academic_readiness_score_reasoning": {"type": "string"}
                }
            }
        },
        "required": ["summary", "profile_features", "scores"]
    }


def create_social_agent_schema() -> Dict[str, Any]:
    """Create JSON schema for SocialAgent output."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Social Agent Output Schema",
        "description": "Schema for SocialAgent output structure",
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "profile_features": {
                "type": "object",
                "properties": {
                    "platforms_found": {
                        "type": "object",
                        "properties": {
                            "facebook": {
                                "type": ["object", "boolean"],
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "present": {"type": "boolean"},
                                            "link": {"type": ["string", "null"]},
                                            "handle": {"type": ["string", "null"]},
                                            "evidence": {"type": "string"}
                                        }
                                    },
                                    {"type": "boolean"}
                                ]
                            },
                            "instagram": {
                                "type": ["object", "boolean"],
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "present": {"type": "boolean"},
                                            "link": {"type": ["string", "null"]},
                                            "handle": {"type": ["string", "null"]},
                                            "evidence": {"type": "string"}
                                        }
                                    },
                                    {"type": "boolean"}
                                ]
                            },
                            "tiktok": {
                                "type": ["object", "boolean"],
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "present": {"type": "boolean"},
                                            "link": {"type": ["string", "null"]},
                                            "handle": {"type": ["string", "null"]},
                                            "evidence": {"type": "string"}
                                        }
                                    },
                                    {"type": "boolean"}
                                ]
                            },
                            "linkedin": {
                                "type": ["object", "boolean"],
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "present": {"type": "boolean"},
                                            "link": {"type": ["string", "null"]},
                                            "handle": {"type": ["string", "null"]},
                                            "evidence": {"type": "string"}
                                        }
                                    },
                                    {"type": "boolean"}
                                ]
                            }
                        }
                    },
                    "total_platforms": {"type": "integer"},
                    "has_professional_presence": {"type": "boolean"},
                    "notes": {"type": "string"}
                }
            },
            "scores": {
                "type": "object",
                "properties": {
                    "social_presence_score": {"type": ["integer", "number"]},
                    "professional_presence_score": {"type": ["integer", "number"]},
                    "overall_score": {"type": ["integer", "number"]}
                },
                "required": ["overall_score"]
            },
            "score_breakdown": {
                "type": "object",
                "properties": {
                    "social_presence_score_reasoning": {"type": "string"},
                    "professional_presence_score_reasoning": {"type": "string"},
                    "overall_score_reasoning": {"type": "string"}
                }
            }
        },
        "required": ["summary", "profile_features", "scores"]
    }


def main():
    """Generate all JSON schemas."""
    schema_dir = get_schema_dir()
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating JSON schemas in: {schema_dir}")
    
    schemas = {
        "application_agent_schema.json": create_application_agent_schema(),
        "personal_agent_schema.json": create_personal_agent_schema(),
        "recommendation_agent_schema.json": create_recommendation_agent_schema(),
        "academic_agent_schema.json": create_academic_agent_schema(),
        "social_agent_schema.json": create_social_agent_schema()
    }
    
    for filename, schema in schemas.items():
        schema_path = schema_dir / filename
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        print(f"  Created: {filename}")
    
    print(f"\nAll schemas generated successfully in {schema_dir}")


if __name__ == "__main__":
    main()

