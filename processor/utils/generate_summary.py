#!/usr/bin/env python3
"""
Generate a summary spreadsheet with applicant information and scores from all profiles.

This script reads all application_profile.json files from the output directory
and generates a CSV/Excel file with applicant details and scores.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import csv

# Load environment variables
load_dotenv()


def extract_applicant_data(application_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract applicant information and scores from application profile.
    
    Args:
        application_profile: The application profile dictionary
        
    Returns:
        Dictionary with extracted data
    """
    profile = application_profile.get('profile', {})
    home_address = profile.get('home_address', {})
    
    # Extract basic information
    data = {
        'first_name': profile.get('first_name') or '',
        'last_name': profile.get('last_name') or '',
        'email': profile.get('email') or '',
        'wai_membership_number': profile.get('wai_membership_number') or '',
        'wai_application_number': profile.get('wai_application_number') or '',
        'country': home_address.get('country') or '',
        'city': home_address.get('city') or '',
    }
    
    # Extract total score summary
    total_score_summary = application_profile.get('total_score_summary', {})
    data['total_score'] = total_score_summary.get('total_score', 0)
    data['total_percentage'] = total_score_summary.get('percentage', 0)
    
    # Extract application scores
    app_scores = application_profile.get('scores', {}) or application_profile.get('score', {})
    data['application_overall_score'] = app_scores.get('overall_score') or app_scores.get('completeness_score', 0)
    data['application_completeness_score'] = app_scores.get('completeness_score', 0)
    
    # Extract personal profile scores
    personal_profile = application_profile.get('personal_profile', {})
    personal_scores = personal_profile.get('scores', {})
    data['personal_overall_score'] = personal_scores.get('overall_score', 0)
    data['personal_motivation_score'] = personal_scores.get('motivation_score', 0)
    data['personal_goals_clarity_score'] = personal_scores.get('goals_clarity_score', 0)
    data['personal_character_score'] = personal_scores.get('character_service_leadership_score', 0)
    
    # Extract recommendation profile scores
    recommendation_profile = application_profile.get('recommendation_profile', {})
    recommendation_scores = recommendation_profile.get('scores', {})
    data['recommendation_overall_score'] = recommendation_scores.get('overall_score', 0)
    data['recommendation_support_strength_score'] = recommendation_scores.get('average_support_strength_score', 0)
    data['recommendation_consistency_score'] = recommendation_scores.get('consistency_of_support_score', 0)
    data['recommendation_depth_score'] = recommendation_scores.get('depth_of_endorsement_score', 0)
    
    # Extract academic profile scores
    academic_profile = application_profile.get('academic_profile', {})
    academic_scores = academic_profile.get('scores', {})
    data['academic_overall_score'] = academic_scores.get('overall_score', 0)
    data['academic_performance_score'] = academic_scores.get('academic_performance_score', 0)
    data['academic_relevance_score'] = academic_scores.get('academic_relevance_score', 0)
    data['academic_readiness_score'] = academic_scores.get('academic_readiness_score', 0)
    
    # Extract social profile scores
    social_profile = application_profile.get('social_profile', {})
    social_scores = social_profile.get('scores', {})
    data['social_overall_score'] = social_scores.get('overall_score', 0)
    data['social_presence_score'] = social_scores.get('social_presence_score', 0)
    data['social_professional_score'] = social_scores.get('professional_presence_score', 0)
    
    return data


def collect_all_applications(output_dir: Path, scholarship_folder: str = None) -> List[Dict[str, Any]]:
    """
    Collect all application profiles from the output directory.
    
    Args:
        output_dir: Base output directory
        scholarship_folder: Optional specific scholarship folder to process
        
    Returns:
        List of dictionaries with application folder path and profile data
    """
    applications = []
    
    if scholarship_folder:
        # Process specific scholarship folder
        scholarship_path = output_dir / scholarship_folder
        if not scholarship_path.exists():
            print(f"ERROR: Scholarship folder not found: {scholarship_path}")
            return applications
        
        for app_folder in scholarship_path.iterdir():
            if app_folder.is_dir() and not app_folder.name.startswith('.'):
                profile_file = app_folder / "application_profile.json"
                if profile_file.exists():
                    try:
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile = json.load(f)
                            applications.append({
                                'scholarship_folder': scholarship_folder,
                                'application_folder': app_folder.name,
                                'profile': profile
                            })
                    except Exception as e:
                        print(f"Warning: Could not read {profile_file}: {e}")
    else:
        # Process all scholarship folders
        for scholarship_dir in output_dir.iterdir():
            if scholarship_dir.is_dir() and not scholarship_dir.name.startswith('.'):
                for app_folder in scholarship_dir.iterdir():
                    if app_folder.is_dir() and not app_folder.name.startswith('.'):
                        profile_file = app_folder / "application_profile.json"
                        if profile_file.exists():
                            try:
                                with open(profile_file, 'r', encoding='utf-8') as f:
                                    profile = json.load(f)
                                    applications.append({
                                        'scholarship_folder': scholarship_dir.name,
                                        'application_folder': app_folder.name,
                                        'profile': profile
                                    })
                            except Exception as e:
                                print(f"Warning: Could not read {profile_file}: {e}")
    
    return applications


def generate_csv(output_file: Path, applications: List[Dict[str, Any]]):
    """
    Generate a CSV file with applicant data and scores.
    
    Args:
        output_file: Path to output CSV file
        applications: List of application data dictionaries
    """
    if not applications:
        print("No applications found to export.")
        return
    
    # Define column order
    columns = [
        'scholarship_folder',
        'application_folder',
        'first_name',
        'last_name',
        'email',
        'wai_membership_number',
        'wai_application_number',
        'country',
        'city',
        'total_score',
        'total_percentage',
        'application_overall_score',
        'application_completeness_score',
        'personal_overall_score',
        'personal_motivation_score',
        'personal_goals_clarity_score',
        'personal_character_score',
        'recommendation_overall_score',
        'recommendation_support_strength_score',
        'recommendation_consistency_score',
        'recommendation_depth_score',
        'academic_overall_score',
        'academic_performance_score',
        'academic_relevance_score',
        'academic_readiness_score',
        'social_overall_score',
        'social_presence_score',
        'social_professional_score',
    ]
    
    # Extract data for all applications
    rows = []
    for app in applications:
        data = extract_applicant_data(app['profile'])
        data['scholarship_folder'] = app['scholarship_folder']
        data['application_folder'] = app['application_folder']
        rows.append(data)
    
    # Write CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Generated CSV file: {output_file}")
    print(f"Exported {len(rows)} applications")


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate a summary spreadsheet with applicant information and scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate summary for all applications
  python code/generate_summary.py
  
  # Generate summary for specific scholarship
  python code/generate_summary.py --scholarship-folder "Delaney_Wings"
  
  # Specify output file
  python code/generate_summary.py --output "summary.csv"
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base output directory (default: from OUTPUT_DATA_DIR env var or 'output')"
    )
    
    parser.add_argument(
        "--scholarship-folder",
        type=str,
        default=None,
        help="Process specific scholarship folder only"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="applicant_scores_summary.csv",
        help="Output CSV file name (default: applicant_scores_summary.csv)"
    )
    
    args = parser.parse_args()
    
    # Get output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(os.getenv("OUTPUT_DATA_DIR", "output"))
    
    if not output_dir.exists():
        print(f"ERROR: Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    # Collect all applications
    print(f"Collecting applications from: {output_dir}")
    applications = collect_all_applications(output_dir, args.scholarship_folder)
    
    if not applications:
        print("No applications found.")
        sys.exit(1)
    
    # Generate CSV
    output_file = Path(args.output)
    generate_csv(output_file, applications)
    
    print(f"\nSummary: {len(applications)} applications exported to {output_file}")


if __name__ == "__main__":
    main()

