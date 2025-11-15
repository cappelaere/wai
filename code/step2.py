#!/usr/bin/env python3
"""
Step 2: Generate Application, Personal, Recommendation, Academic, and Social Profiles

This script processes extracted application form data and attachments from Step 1
to generate:
- Application profiles from application forms
- Personal profiles from essays and resumes
- Recommendation profiles from recommendation letters
- Academic profiles from resumes and academic documents
- Social presence profiles from resumes and essays (Facebook, Instagram, TikTok, LinkedIn)

It reads:
- application_form_data.json (from Step 1)
- application_form_text.txt (from Step 1)
- attachments.json (from Step 1)

And generates:
- application_profile.json
- personal_profile.json
- recommendation_profile.json
- academic_profile.json
- social_profile.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from application_agent import ApplicationAgent
from personal_agent import PersonalAgent
from recommendation_agent import RecommendationAgent
from academic_agent import AcademicAgent
from social_agent import SocialAgent

# Import logging utilities
from logging_utils import execution_logger, log_exception, log_summary

# Import multiprocessing support
from processing_pool import ProcessingPool

# Load environment variables from .env file
load_dotenv()


def load_personal_criteria_from_output(output_dir: Path) -> Optional[str]:
    """
    Try to find personal_criteria.txt by looking for input folder relative to output directory.
    Assumes output is at: {scholarship}/output/ and input is at: {scholarship}/input/
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        Criteria text as string, or None if file doesn't exist
    """
    # Try to find the scholarship folder by going up from output directory
    # Common structure: scholarship_folder/output/ or scholarship_folder/applications/output/
    current = output_dir.resolve()
    
    # Look for input folder at various levels
    possible_paths = [
        current.parent / "input" / "personal_criteria.txt",  # output/../input/
        current.parent.parent / "input" / "personal_criteria.txt",  # output/../../input/
        current.parent.parent.parent / "input" / "personal_criteria.txt",  # output/../../../input/
    ]
    
    for criteria_file in possible_paths:
        if criteria_file.exists():
            try:
                with open(criteria_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read personal_criteria.txt from {criteria_file}: {e}")
                return None
    
    return None


def load_recommendation_criteria_from_output(output_dir: Path) -> Optional[str]:
    """
    Try to find recommendation_criteria.txt by looking for input folder relative to output directory.
    Assumes output is at: {scholarship}/output/ and input is at: {scholarship}/input/
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        Criteria text as string, or None if file doesn't exist
    """
    # Try to find the scholarship folder by going up from output directory
    # Common structure: scholarship_folder/output/ or scholarship_folder/applications/output/
    current = output_dir.resolve()
    
    # Look for input folder at various levels
    possible_paths = [
        current.parent / "input" / "recommendation_criteria.txt",  # output/../input/
        current.parent.parent / "input" / "recommendation_criteria.txt",  # output/../../input/
        current.parent.parent.parent / "input" / "recommendation_criteria.txt",  # output/../../../input/
    ]
    
    for criteria_file in possible_paths:
        if criteria_file.exists():
            try:
                with open(criteria_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read recommendation_criteria.txt from {criteria_file}: {e}")
                return None
    
    return None


def load_academic_criteria_from_output(output_dir: Path, scholarship_folder_name: Optional[str] = None) -> Optional[str]:
    """
    Try to find academic_criteria.txt by looking for input folder.
    New structure: {OUTPUT_DATA_DIR}/{scholarship_folder_name}/{application_folder}/
                   {INPUT_DATA_DIR}/{scholarship_folder_name}/input/
    
    Args:
        output_dir: Path to the output directory (base OUTPUT_DATA_DIR)
        scholarship_folder_name: Name of the scholarship folder (e.g., 'Delaney_Wings')
    """
    if scholarship_folder_name:
        # Use INPUT_DATA_DIR to construct path
        input_data_dir = os.getenv("INPUT_DATA_DIR", "data/2026")
        criteria_path = Path(input_data_dir) / scholarship_folder_name / "input" / "academic_criteria.txt"
        if criteria_path.exists():
            try:
                with open(criteria_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read academic_criteria.txt from {criteria_path}: {e}")
                return None
    
    # Fallback: Try to find by going up from output directory (old structure)
    current = output_dir.resolve()
    possible_paths = [
        current.parent / "input" / "academic_criteria.txt",
        current.parent.parent / "input" / "academic_criteria.txt",
        current.parent.parent.parent / "input" / "academic_criteria.txt",
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read academic_criteria.txt from {path}: {e}")
                continue
    
    return None


def load_social_criteria_from_output(output_dir: Path, scholarship_folder_name: Optional[str] = None) -> Optional[str]:
    """
    Try to find social_criteria.txt by looking for input folder.
    New structure: {OUTPUT_DATA_DIR}/{scholarship_folder_name}/{application_folder}/
                   {INPUT_DATA_DIR}/{scholarship_folder_name}/input/
    
    Args:
        output_dir: Path to the output directory (base OUTPUT_DATA_DIR)
        scholarship_folder_name: Name of the scholarship folder (e.g., 'Delaney_Wings')
    """
    if scholarship_folder_name:
        # Use INPUT_DATA_DIR to construct path
        input_data_dir = os.getenv("INPUT_DATA_DIR", "data/2026")
        criteria_path = Path(input_data_dir) / scholarship_folder_name / "input" / "social_criteria.txt"
        if criteria_path.exists():
            try:
                with open(criteria_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read social_criteria.txt from {criteria_path}: {e}")
                return None
    
    # Fallback: Try to find by going up from output directory (old structure)
    current = output_dir.resolve()
    possible_paths = [
        current.parent / "input" / "social_criteria.txt",
        current.parent.parent / "input" / "social_criteria.txt",
        current.parent.parent.parent / "input" / "social_criteria.txt",
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read social_criteria.txt from {path}: {e}")
                continue
    
    return None


def load_application_criteria_from_output(output_dir: Path, scholarship_folder_name: Optional[str] = None) -> Optional[str]:
    """
    Try to find application_criteria.txt by looking for input folder.
    New structure: {OUTPUT_DATA_DIR}/{scholarship_folder_name}/{application_folder}/
                   {INPUT_DATA_DIR}/{scholarship_folder_name}/input/
    
    Args:
        output_dir: Path to the output directory (base OUTPUT_DATA_DIR)
        scholarship_folder_name: Name of the scholarship folder (e.g., 'Delaney_Wings')
    """
    if scholarship_folder_name:
        # Use INPUT_DATA_DIR to construct path
        input_data_dir = os.getenv("INPUT_DATA_DIR", "data/2026")
        criteria_path = Path(input_data_dir) / scholarship_folder_name / "input" / "application_criteria.txt"
        if criteria_path.exists():
            try:
                with open(criteria_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read application_criteria.txt from {criteria_path}: {e}")
                return None
    
    # Fallback: Try to find by going up from output directory (old structure)
    current = output_dir.resolve()
    possible_paths = [
        current.parent / "input" / "application_criteria.txt",
        current.parent.parent / "input" / "application_criteria.txt",
        current.parent.parent.parent / "input" / "application_criteria.txt",
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Could not read application_criteria.txt from {path}: {e}")
                continue
    
    return None


def process_single_application_step2(
    output_folder: str,
    model_name: str,
    verbose: bool = True,
    additional_criteria: Optional[str] = None,
    recommendation_criteria: Optional[str] = None,
    application_criteria: Optional[str] = None,
    academic_criteria: Optional[str] = None,
    social_criteria: Optional[str] = None
) -> dict:
    """
    Process Step 2 for a single application folder.
    
    Args:
        output_folder: Path to the output folder containing Step 1 results
        model_name: Ollama model name to use
        verbose: Whether to print progress messages
        additional_criteria: Optional additional criteria text for PersonalAgent (from personal_criteria.txt)
        recommendation_criteria: Optional additional criteria text for RecommendationAgent (from recommendation_criteria.txt)
        application_criteria: Optional additional criteria text for ApplicationAgent (from application_criteria.txt)
        academic_criteria: Optional additional criteria text for AcademicAgent (from academic_criteria.txt)
        social_criteria: Optional additional criteria text for SocialAgent (from social_criteria.txt)
        
    Returns:
        Dictionary with processing result
    """
    output_path = Path(output_folder)
    application_folder = output_path.name
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing Step 2 for: {application_folder}")
        print(f"{'='*60}")
    
    try:
        # Check for required Step 1 files
        # Support both new format (application_form_data.json + application_form_text.txt) 
        # and old format (application_profile.json) for backward compatibility
        application_form_data_file = output_path / "application_form_data.json"
        application_form_text_file = output_path / "application_form_text.txt"
        old_application_profile_file = output_path / "application_profile.json"
        attachments_file = output_path / "attachments.json"
        
        # Check for new format files
        has_new_format = application_form_data_file.exists() and application_form_text_file.exists()
        # Check for old format file
        has_old_format = old_application_profile_file.exists()
        
        if not has_new_format and not has_old_format:
            error_msg = f"ERROR: Neither application_form_data.json/application_form_text.txt (new format) nor application_profile.json (old format) found in {output_folder}"
            if verbose:
                print(f"   {error_msg}")
            return {
                "success": False,
                "folder": application_folder,
                "error": error_msg
            }
        
        if not attachments_file.exists():
            error_msg = f"ERROR: attachments.json not found in {output_folder}"
            if verbose:
                print(f"   {error_msg}")
            return {
                "success": False,
                "folder": application_folder,
                "error": error_msg
            }
        
        # Load Step 1 results
        if verbose:
            print("\n1. Loading Step 1 results...")
        
        if has_new_format:
            # New format: load from separate files
            with open(application_form_data_file, 'r', encoding='utf-8') as f:
                application_form_data = json.load(f)
            
            with open(application_form_text_file, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
            
            file_list = application_form_data.get('file_list', [])
            if verbose:
                print(f"   Loaded new format: application_form_data.json and application_form_text.txt")
        else:
            # Old format: extract from application_profile.json
            with open(old_application_profile_file, 'r', encoding='utf-8') as f:
                old_profile = json.load(f)
            
            # Extract text from old profile (we'll need to reconstruct it)
            # For old format, we'll use the profile summary and try to extract text
            # This is a fallback - ideally users should re-run step1
            extracted_text = old_profile.get('summary', '') + "\n\n" + json.dumps(old_profile.get('profile', {}), indent=2)
            
            # Try to get file list from old profile if available
            file_list = []
            if 'attachments' in old_profile:
                file_list = [att.get('filename', '') for att in old_profile.get('attachments', [])]
            
            if verbose:
                print(f"   Loaded old format: application_profile.json (consider re-running step1 for full functionality)")
        
        with open(attachments_file, 'r', encoding='utf-8') as f:
            attachments_data = json.load(f)
        
        classified_attachments = attachments_data.get('attachments', [])
        
        if verbose:
            print(f"   Loaded application form data, text ({len(extracted_text)} chars), and {len(classified_attachments)} attachments")
        
        # Step 2: Generate Application Profile
        if verbose:
            print("\n2. Generating Application Profile...")
        
        try:
            application_agent = ApplicationAgent(model_name=model_name)
            application_profile = application_agent.analyze_application(
                extracted_text, 
                file_list, 
                additional_criteria=application_criteria
            )
            
            # Save application profile
            application_profile_file = output_path / "application_profile.json"
            with open(application_profile_file, 'w') as f:
                json.dump(application_profile, f, indent=2)
            
            if verbose:
                overall_score = application_profile.get('scores', {}).get('overall_score', 
                    application_profile.get('score', {}).get('completeness_score', 'N/A'))  # Backward compatibility
                print(f"   Application profile generated (overall score: {overall_score})")
                print(f"   Saved to: {application_profile_file.name}")
        except Exception as e:
            error_msg = f"Warning: Failed to generate application profile: {str(e)}"
            if verbose:
                print(f"   {error_msg}")
            application_profile = {
                "error": error_msg,
                "summary": "Application profile generation failed",
                "profile": {},
                "score": {}
            }
        
        # Step 3: Generate Personal Profile
        if verbose:
            print("\n3. Generating Personal Profile...")
        
        # Filter attachments by category
        essays = [att for att in classified_attachments if att.get('category') == 'essay']
        resume = next((att for att in classified_attachments if att.get('category') == 'resume'), None)
        
        if verbose:
            print(f"   Found {len(essays)} essay(s) and {'1 resume' if resume else 'no resume'}")
        
        # Only process if we have essays or resume
        if essays or resume:
            personal_agent = PersonalAgent(model_name=model_name)
            personal_profile = personal_agent.analyze_personal_profile(
                essays=essays,
                resume=resume,
                application_profile=application_profile,
                text_files_base_path=output_path,
                additional_criteria=additional_criteria
            )
            
            if verbose:
                overall_score = personal_profile.get('scores', {}).get('overall_score', 'N/A')
                print(f"   Personal profile generated (overall score: {overall_score})")
        else:
            if verbose:
                print("   No essays or resume found - creating empty personal profile")
            personal_profile = {
                "summary": "No essays or resume available for personal profile analysis",
                "profile_features": {},
                "scores": {
                    "motivation_score": 0,
                    "goals_clarity_score": 0,
                    "character_service_leadership_score": 0,
                    "overall_score": 0
                },
                "score_breakdown": {}
            }
        
        # Save personal profile
        personal_profile_file = output_path / "personal_profile.json"
        with open(personal_profile_file, 'w') as f:
            json.dump(personal_profile, f, indent=2)
        
        if verbose:
            print(f"\n   Personal profile saved to: {personal_profile_file}")
        
        # Step 4: Generate Recommendation Profile
        if verbose:
            print("\n4. Generating Recommendation Profile...")
        
        # Filter attachments by category for recommendations
        recommendations = [att for att in classified_attachments if att.get('category') == 'recommendation']
        
        if verbose:
            print(f"   Found {len(recommendations)} recommendation letter(s)")
        
        # Only process if we have recommendations
        if recommendations:
            recommendation_agent = RecommendationAgent(model_name=model_name)
            recommendation_profile = recommendation_agent.analyze_recommendation_profile(
                recommendations=recommendations,
                application_profile=application_profile,
                text_files_base_path=output_path,
                additional_criteria=recommendation_criteria
            )
            
            if verbose:
                overall_score = recommendation_profile.get('scores', {}).get('overall_score', 'N/A')
                print(f"   Recommendation profile generated (overall score: {overall_score})")
        else:
            if verbose:
                print("   No recommendation letters found - creating empty recommendation profile")
            recommendation_profile = {
                "summary": "No recommendation letters available for recommendation profile analysis",
                "profile_features": {},
                "scores": {
                    "average_support_strength_score": 0,
                    "consistency_of_support_score": 0,
                    "depth_of_endorsement_score": 0,
                    "overall_score": 0
                },
                "score_breakdown": {}
            }
        
        # Save recommendation profile
        recommendation_profile_file = output_path / "recommendation_profile.json"
        with open(recommendation_profile_file, 'w') as f:
            json.dump(recommendation_profile, f, indent=2)
        
        if verbose:
            print(f"\n   Recommendation profile saved to: {recommendation_profile_file}")
        
        # Step 5: Generate Academic Profile
        if verbose:
            print("\n5. Generating Academic Profile...")
        
        # Get resume for education section
        resume = next((att for att in classified_attachments if att.get('category') == 'resume'), None)
        
        # Filter for potential academic attachments (transcripts, grade summaries, etc.)
        academic_keywords = ['transcript', 'grade', 'gpa', 'academic', 'diploma', 'degree', 'certificate', 'report card']
        academic_attachments = []
        for att in classified_attachments:
            filename_lower = att.get('filename', '').lower()
            # Include if it's classified as unknown and has academic keywords, or if explicitly academic
            if (att.get('category') == 'unknown' and 
                any(keyword in filename_lower for keyword in academic_keywords)):
                academic_attachments.append(att)
            # Also check if the category might be academic (for future expansion)
            elif att.get('category') == 'transcript' or att.get('category') == 'academic':
                academic_attachments.append(att)
        
        if verbose:
            print(f"   Found {'1 resume' if resume else 'no resume'} and {len(academic_attachments)} academic document(s)")
        
        # Process academic profile (always try, even without attachments, as resume and application form have info)
        try:
            academic_agent = AcademicAgent(model_name=model_name)
            academic_profile = academic_agent.analyze_academic_profile(
                resume=resume,
                academic_attachments=academic_attachments,
                application_profile=application_profile,
                text_files_base_path=output_path,
                additional_criteria=academic_criteria
            )
            
            if verbose:
                overall_score = academic_profile.get('scores', {}).get('overall_score', 'N/A')
                print(f"   Academic profile generated (overall score: {overall_score})")
        except Exception as e:
            error_msg = f"Warning: Failed to generate academic profile: {str(e)}"
            if verbose:
                print(f"   {error_msg}")
            academic_profile = {
                "error": error_msg,
                "summary": "Academic profile generation failed",
                "profile_features": {},
                "scores": {},
                "score_breakdown": {}
            }
        
        # Save academic profile
        academic_profile_file = output_path / "academic_profile.json"
        with open(academic_profile_file, 'w') as f:
            json.dump(academic_profile, f, indent=2)
        
        if verbose:
            print(f"\n   Academic profile saved to: {academic_profile_file}")
        
        # Step 6: Generate Social Presence Profile
        if verbose:
            print("\n6. Generating Social Presence Profile...")
        
        # Filter attachments by category for social analysis
        essays = [att for att in classified_attachments if att.get('category') == 'essay']
        resume = next((att for att in classified_attachments if att.get('category') == 'resume'), None)
        
        if verbose:
            print(f"   Analyzing social media presence from {'1 resume' if resume else 'no resume'} and {len(essays)} essay(s)")
        
        # Process social profile (always try, even without attachments, as application form may have info)
        try:
            social_agent = SocialAgent(model_name=model_name)
            social_profile = social_agent.analyze_social_presence(
                resume=resume,
                essays=essays,
                application_profile=application_profile,
                text_files_base_path=output_path,
                additional_criteria=social_criteria
            )
            
            if verbose:
                overall_score = social_profile.get('scores', {}).get('overall_score', 'N/A')
                platforms_found = social_profile.get('profile_features', {}).get('total_platforms', 0)
                print(f"   Social profile generated (overall score: {overall_score}, platforms found: {platforms_found})")
        except Exception as e:
            error_msg = f"Warning: Failed to generate social profile: {str(e)}"
            if verbose:
                print(f"   {error_msg}")
            social_profile = {
                "error": error_msg,
                "summary": "Social profile generation failed",
                "profile_features": {},
                "scores": {},
                "score_breakdown": {}
            }
        
        # Save social profile
        social_profile_file = output_path / "social_profile.json"
        with open(social_profile_file, 'w') as f:
            json.dump(social_profile, f, indent=2)
        
        if verbose:
            print(f"\n   Social profile saved to: {social_profile_file}")
        
        # Calculate total score summary
        scores = {
            "application": application_profile.get('scores', {}).get('overall_score', 
                application_profile.get('score', {}).get('completeness_score', 0)),  # Backward compatibility
            "personal": personal_profile.get('scores', {}).get('overall_score', 0),
            "recommendation": recommendation_profile.get('scores', {}).get('overall_score', 0),
            "academic": academic_profile.get('scores', {}).get('overall_score', 0),
            "social": social_profile.get('scores', {}).get('overall_score', 0)
        }
        
        # Convert string scores to numbers if needed
        for key, value in scores.items():
            if isinstance(value, str) and value != 'N/A':
                try:
                    scores[key] = float(value)
                except (ValueError, TypeError):
                    scores[key] = 0
            elif not isinstance(value, (int, float)):
                scores[key] = 0
        
        total_score = sum(scores.values())
        max_possible_score = 500  # 5 profiles * 100 points each
        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        total_score_summary = {
            "total_score": round(total_score, 2),
            "max_possible_score": max_possible_score,
            "percentage": round(percentage, 2),
            "score_breakdown": {
                "application_score": round(scores['application'], 2),
                "personal_score": round(scores['personal'], 2),
                "recommendation_score": round(scores['recommendation'], 2),
                "academic_score": round(scores['academic'], 2),
                "social_score": round(scores['social'], 2)
            }
        }
        
        # Update application profile with all profiles and total score summary
        application_profile['personal_profile'] = personal_profile
        application_profile['recommendation_profile'] = recommendation_profile
        application_profile['academic_profile'] = academic_profile
        application_profile['social_profile'] = social_profile
        application_profile['total_score_summary'] = total_score_summary
        
        with open(application_profile_file, 'w') as f:
            json.dump(application_profile, f, indent=2)
        
        if verbose:
            print(f"   Updated application_profile.json with all profiles (application, personal, recommendation, academic, social)")
            print(f"   Total score summary: {total_score_summary['total_score']}/{max_possible_score} ({total_score_summary['percentage']}%)")
        
        # Extract scholarship folder name from path
        # Path structure: {OUTPUT_DATA_DIR}/{scholarship_folder}/{application_folder}
        scholarship_folder_name = ''
        try:
            # output_path is the application folder, parent should be scholarship folder
            if output_path.parent and output_path.parent != output_path:
                scholarship_folder_name = output_path.parent.name
        except:
            pass
        
        return {
            "success": True,
            "folder": application_folder,
            "scholarship_folder": scholarship_folder_name,
            "application_profile_file": str(application_profile_file),
            "personal_profile_file": str(personal_profile_file),
            "recommendation_profile_file": str(recommendation_profile_file),
            "academic_profile_file": str(academic_profile_file),
            "social_profile_file": str(social_profile_file),
            "application_profile": application_profile,
            "personal_profile": personal_profile,
            "recommendation_profile": recommendation_profile,
            "academic_profile": academic_profile,
            "social_profile": social_profile
        }
        
    except Exception as e:
        error_msg = f"ERROR: {str(e)}"
        if verbose:
            print(f"   {error_msg}")
        log_exception(e, "step2.py", f"process_single_application_step2: {application_folder}")
        return {
            "success": False,
            "folder": application_folder,
            "error": error_msg
        }


def _worker_process_application_step2(args_tuple) -> dict:
    """
    Worker function for multiprocessing.

    Must be at module level (not nested) to be picklable.
    Accepts a tuple of arguments since multiprocessing map can only pass one argument per worker.

    Args:
        args_tuple: (output_folder, model_name, personal_criteria, recommendation_criteria,
                     application_criteria, academic_criteria, social_criteria, verbose)

    Returns:
        Result dictionary from process_single_application_step2
    """
    (output_folder, model_name, personal_criteria, recommendation_criteria,
     application_criteria, academic_criteria, social_criteria, verbose) = args_tuple
    return process_single_application_step2(
        output_folder=output_folder,
        model_name=model_name,
        verbose=False,  # Disable verbose in worker to avoid log spam
        additional_criteria=personal_criteria,
        recommendation_criteria=recommendation_criteria,
        application_criteria=application_criteria,
        academic_criteria=academic_criteria,
        social_criteria=social_criteria
    )


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Step 2: Generate Application, Personal, Recommendation, Academic, and Social Profiles from Step 1 results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all applications in output directory (default)
  python code/step2.py --scholarship-folder "Delaney_Wings"
  
  # Process first 5 applications only
  python code/step2.py --scholarship-folder "Delaney_Wings" --limit 5
  
  # Process a specific application folder
  python code/step2.py --scholarship-folder "Delaney_Wings" --application-folder "75179"
  
  # Process with custom model
  python code/step2.py --scholarship-folder "Delaney_Wings" --limit 3 --model mistral
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory path to append to OUTPUT_DATA_DIR (default: uses OUTPUT_DATA_DIR directly). Example: if OUTPUT_DATA_DIR='output/2026' and --output-dir='Delaney_Wings', looks in 'output/2026/Delaney_Wings'"
    )
    
    parser.add_argument(
        "--scholarship-folder",
        type=str,
        default=None,
        help="Process applications from a specific scholarship folder in output (e.g., 'Delaney_Wings'). Looks in {OUTPUT_DATA_DIR}/{scholarship-folder}/. If not specified, processes all scholarship folders found in output directory."
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Path to input folder containing criteria files (default: uses INPUT_DATA_DIR/{scholarship_folder}/input)"
    )
    
    parser.add_argument(
        "--application-folder",
        type=str,
        default=None,
        help="Process a specific application folder (by name). If not specified, processes all folders."
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of application folders to process (default: 0 = process all, use --limit N to limit to N applications)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model name to use (default: from OLLAMA_MODEL env var or 'llama3.2')"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output (only show errors and summary)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of worker processes for parallel processing (default: 0 = sequential). Set to > 0 to enable multiprocessing. Profile generation uses threading (I/O-bound) so you can use more workers than CPU count."
    )

    args = parser.parse_args()
    
    # Get configuration from arguments or environment variables
    # Use OUTPUT_DATA_DIR from environment
    base_output_dir = Path(os.getenv("OUTPUT_DATA_DIR", "output"))
    if args.output_dir:
        # Use specified output_dir as absolute path or relative to current directory
        output_dir = Path(args.output_dir)
    else:
        output_dir = base_output_dir
    
    model_name = args.model or os.getenv("OLLAMA_MODEL", "llama3.2")
    verbose = not args.quiet
    
    if not output_dir.exists():
        print(f"ERROR: Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    if not output_dir.is_dir():
        print(f"ERROR: Path is not a directory: {output_dir}")
        sys.exit(1)
    
    # Note: Criteria will be loaded per scholarship folder below
    personal_criteria = None
    recommendation_criteria = None
    application_criteria = None
    academic_criteria = None
    social_criteria = None
    
    # Find scholarship folders in output directory
    # New structure: {OUTPUT_DATA_DIR}/{scholarship_folder_name}/{application_folder}/
    scholarship_folders = []
    if args.scholarship_folder:
        # Process specific scholarship folder
        scholarship_path = output_dir / args.scholarship_folder
        if scholarship_path.exists() and scholarship_path.is_dir():
            scholarship_folders = [(args.scholarship_folder, scholarship_path)]
        else:
            print(f"ERROR: Scholarship folder not found: {scholarship_path}")
            sys.exit(1)
    else:
        # Find all scholarship folders (subdirectories that contain application folders)
        for item in output_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if this looks like a scholarship folder (contains application folders)
                has_applications = False
                try:
                    for app_dir in item.iterdir():
                        if app_dir.is_dir() and not app_dir.name.startswith('.'):
                            # Check if this application folder has the required files
                            if ((app_dir / "application_form_data.json").exists() or
                                (app_dir / "application_profile.json").exists()):
                                has_applications = True
                                break
                except Exception as e:
                    if verbose:
                        print(f"Warning: Error checking {item.name}: {e}")
                    continue
                
                if has_applications:
                    scholarship_folders.append((item.name, item))
    
    if not scholarship_folders:
        print(f"ERROR: No scholarship folders found in {output_dir}")
        sys.exit(1)
    
    # Print summary
    if verbose:
        print("=" * 60)
        print("Step 2: Profile Generation")
        print("=" * 60)
        print(f"Output directory: {output_dir}")
        print(f"Scholarship folders to process: {len(scholarship_folders)}")
        print(f"Model: {model_name}")
        if args.limit and args.limit > 0:
            print(f"Limit: {args.limit} applications per scholarship")
        else:
            print(f"Limit: all (default)")
        print("=" * 60)
    
    # Process each scholarship folder
    all_results = []
    total_successful = 0
    total_failed = 0
    
    for scholarship_name, scholarship_path in scholarship_folders:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing scholarship: {scholarship_name}")
            print(f"{'='*60}")
        
        # Load criteria for this scholarship
        # Criteria should be in INPUT_DATA_DIR/{scholarship_folder}/input
        if args.input_dir:
            # Use explicitly provided input directory
            input_path = Path(args.input_dir)
        else:
            # Use INPUT_DATA_DIR/{scholarship_folder}/input
            input_data_dir = os.getenv("INPUT_DATA_DIR", "data/2026")
            input_path = Path(input_data_dir) / scholarship_name / "input"
        
        # Load all criteria files
        personal_criteria = None
        recommendation_criteria = None
        application_criteria = None
        academic_criteria = None
        social_criteria = None
        
        if args.input_dir or input_path.exists():
            for criteria_name, criteria_var in [
                ("personal_criteria.txt", "personal_criteria"),
                ("recommendation_criteria.txt", "recommendation_criteria"),
                ("application_criteria.txt", "application_criteria"),
                ("academic_criteria.txt", "academic_criteria"),
                ("social_criteria.txt", "social_criteria"),
            ]:
                criteria_file = input_path / criteria_name
                if criteria_file.exists():
                    try:
                        with open(criteria_file, 'r', encoding='utf-8') as f:
                            if criteria_var == "personal_criteria":
                                personal_criteria = f.read().strip()
                            elif criteria_var == "recommendation_criteria":
                                recommendation_criteria = f.read().strip()
                            elif criteria_var == "application_criteria":
                                application_criteria = f.read().strip()
                            elif criteria_var == "academic_criteria":
                                academic_criteria = f.read().strip()
                            elif criteria_var == "social_criteria":
                                social_criteria = f.read().strip()
                        if verbose:
                            print(f"Loaded {criteria_name} from: {criteria_file}")
                    except Exception as e:
                        print(f"Warning: Could not read {criteria_name} from {criteria_file}: {e}")
        else:
            # Fallback: try old structure
            personal_criteria = load_personal_criteria_from_output(output_dir, scholarship_name)
            recommendation_criteria = load_recommendation_criteria_from_output(output_dir, scholarship_name)
            application_criteria = load_application_criteria_from_output(output_dir, scholarship_name)
            academic_criteria = load_academic_criteria_from_output(output_dir, scholarship_name)
            social_criteria = load_social_criteria_from_output(output_dir, scholarship_name)
        
        # Find application folders in this scholarship folder
        if args.application_folder:
            application_folders = [args.application_folder]
        else:
            application_folders = [
                item.name for item in scholarship_path.iterdir()
                if item.is_dir() 
                and not item.name.startswith('.')
                and (
                    (item / "application_form_data.json").exists() or 
                    (item / "application_profile.json").exists()
                )
                and (item / "attachments.json").exists()
            ]
            
            # Sort folders: numeric folders first (sorted numerically), then non-numeric (sorted alphabetically)
            def sort_key(folder_name):
                """Sort key: numeric folders sorted as integers, non-numeric sorted alphabetically."""
                if folder_name.isdigit():
                    return (0, int(folder_name))
                else:
                    return (1, folder_name)
            
            application_folders.sort(key=sort_key)
            
            # Apply limit (default is 0 = all, unless --limit N is specified)
            if args.limit and args.limit > 0:
                application_folders = application_folders[:args.limit]
        
        if not application_folders:
            if verbose:
                print(f"  No application folders found in {scholarship_name}")
            continue
        
        if verbose:
            print(f"  Found {len(application_folders)} application folders")
        
        # Prepare arguments for multiprocessing
        # Note: Step 2 uses multiple criteria arguments
        worker_args = [
            (
                str(scholarship_path / app_folder),
                model_name,
                personal_criteria,
                recommendation_criteria,
                application_criteria,
                academic_criteria,
                social_criteria,
                verbose
            )
            for app_folder in application_folders
        ]

        # Process using pool (use threading for I/O-bound Ollama API calls)
        if verbose and args.workers > 0:
            print(f"\n  Using {args.workers} worker threads for parallel processing")

        with ProcessingPool(num_workers=args.workers, use_threading=True, verbose=verbose) as pool:
            if verbose and len(application_folders) > 1:
                print(f"  Processing {len(application_folders)} applications...")
            results = pool.map_unordered(
                _worker_process_application_step2,
                worker_args,
                show_progress=verbose
            )

        # Consolidate results
        all_results.extend(results)
        total_successful += sum(1 for r in results if r.get("success", False))
        total_failed += sum(1 for r in results if not r.get("success", False))

        if verbose and total_failed > 0:
            for result in results:
                if not result.get("success", False):
                    print(f"  ERROR: {result.get('error', 'Unknown error')}")
    
    # Print final summary
    if verbose:
        print("\n" + "=" * 60)
        print("Processing Summary")
        print("=" * 60)
        print(f"Total processed: {len(all_results)}")
        print(f"Successful: {total_successful}")
        print(f"Failed: {total_failed}")
        
        if total_failed > 0:
            print("\nFailed applications:")
            for result in all_results:
                if not result["success"]:
                    print(f"  - {result.get('folder', 'Unknown')}: {result.get('error', 'Unknown error')}")
        print("=" * 60)
    
    # Log summary
    summary = {
        "total_processed": len(all_results),
        "successful": total_successful,
        "failed": total_failed
    }
    if total_failed > 0:
        failed_folders = [r.get('folder', 'Unknown') for r in all_results if not r["success"]]
        summary["failed_folders"] = failed_folders
    
    log_summary("step2.py", summary)
    
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    try:
        # Parse arguments first to get script name and args for logging
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--scholarship-folder", type=str, default=None)
        parser.add_argument("--application-folder", type=str, default=None)
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--model", type=str, default=None)
        parser.add_argument("--output-dir", type=str, default=None)
        parser.add_argument("--quiet", action="store_true")
        
        # Parse known args only (don't error on unknown)
        args, _ = parser.parse_known_args()
        
        # Prepare args dict for logging
        log_args = {
            "scholarship_folder": args.scholarship_folder,
            "application_folder": args.application_folder,
            "limit": args.limit if (args.limit and args.limit > 0) else "all",
            "model": args.model,
            "output_dir": args.output_dir,
            "quiet": args.quiet
        }
        
        # Use execution logger
        with execution_logger("step2.py", log_args):
            main()
    except Exception as e:
        log_exception(e, "step2.py", "main execution")
        raise

