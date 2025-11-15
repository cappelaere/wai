#!/usr/bin/env python3
"""
Step 3: Generate Review Board Reports

This script generates one-page markdown reports for each application
to be used by the review board. Each report includes:
- Applicant information
- WAI number
- Total score and summary
- Breakdown by agent with scores and summaries
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from collections import defaultdict
from dotenv import load_dotenv

# Import logging utilities
from processor.utils.logging_utils import execution_logger, log_exception, log_summary

# Load environment variables
load_dotenv()


def load_template(template_path: Optional[Path] = None) -> str:
    """
    Load the report template from file or use default.
    
    Args:
        template_path: Optional path to custom template file
        
    Returns:
        Template string with placeholders
    """
    if template_path and template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Default template location: code/templates/review_report_template.md
    default_template_path = Path(__file__).parent / "templates" / "review_report_template.md"
    if default_template_path.exists():
        with open(default_template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Fallback: return error message as template if default template not found
    return """# Error: Template Not Found

The default template file could not be found at: code/templates/review_report_template.md

Please specify a template file using --template option.
"""


def extract_report_data(application_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all data needed for the report from application profile.
    
    Args:
        application_profile: The application profile dictionary
        
    Returns:
        Dictionary with all report data
    """
    profile = application_profile.get('profile', {})
    home_address = profile.get('home_address', {})
    
    # Basic information
    data = {
        'first_name': profile.get('first_name') or 'N/A',
        'last_name': profile.get('last_name') or 'N/A',
        'email': profile.get('email') or 'N/A',
        'wai_membership_number': profile.get('wai_membership_number') or 'N/A',
        'wai_application_number': profile.get('wai_application_number') or 'N/A',
        'country': home_address.get('country') or 'N/A',
        'city': home_address.get('city') or 'N/A',
    }
    
    # Total score summary
    total_score_summary = application_profile.get('total_score_summary', {})
    data['total_score'] = total_score_summary.get('total_score', 0)
    data['max_possible_score'] = total_score_summary.get('max_possible_score', 500)
    data['total_percentage'] = total_score_summary.get('percentage', 0)
    
    # Overall summary (from application profile)
    data['overall_summary'] = application_profile.get('summary', 'No summary available.')
    
    # Application profile
    app_scores = application_profile.get('scores', {}) or application_profile.get('score', {})
    data['application_overall_score'] = app_scores.get('overall_score') or app_scores.get('completeness_score', 0)
    data['application_summary'] = application_profile.get('summary', 'No application summary available.')
    
    # Personal profile
    personal_profile = application_profile.get('personal_profile', {})
    personal_scores = personal_profile.get('scores', {})
    data['personal_overall_score'] = personal_scores.get('overall_score', 0)
    data['personal_summary'] = personal_profile.get('summary', 'No personal profile available.')
    data['personal_motivation_score'] = personal_scores.get('motivation_score', 0)
    data['personal_goals_clarity_score'] = personal_scores.get('goals_clarity_score', 0)
    data['personal_character_score'] = personal_scores.get('character_service_leadership_score', 0)
    
    # Recommendation profile
    recommendation_profile = application_profile.get('recommendation_profile', {})
    recommendation_scores = recommendation_profile.get('scores', {})
    data['recommendation_overall_score'] = recommendation_scores.get('overall_score', 0)
    data['recommendation_summary'] = recommendation_profile.get('summary', 'No recommendation profile available.')
    data['recommendation_support_strength_score'] = recommendation_scores.get('average_support_strength_score', 0)
    data['recommendation_consistency_score'] = recommendation_scores.get('consistency_of_support_score', 0)
    data['recommendation_depth_score'] = recommendation_scores.get('depth_of_endorsement_score', 0)
    
    # Academic profile
    academic_profile = application_profile.get('academic_profile', {})
    academic_scores = academic_profile.get('scores', {})
    data['academic_overall_score'] = academic_scores.get('overall_score', 0)
    data['academic_summary'] = academic_profile.get('summary', 'No academic profile available.')
    data['academic_performance_score'] = academic_scores.get('academic_performance_score', 0)
    data['academic_relevance_score'] = academic_scores.get('academic_relevance_score', 0)
    data['academic_readiness_score'] = academic_scores.get('academic_readiness_score', 0)
    
    # Social profile
    social_profile = application_profile.get('social_profile', {})
    social_scores = social_profile.get('scores', {})
    data['social_overall_score'] = social_scores.get('overall_score', 0)
    data['social_summary'] = social_profile.get('summary', 'No social profile available.')
    data['social_presence_score'] = social_scores.get('social_presence_score', 0)
    data['social_professional_score'] = social_scores.get('professional_presence_score', 0)
    
    # Extract social media links
    profile_features = social_profile.get('profile_features', {})
    platforms_found = profile_features.get('platforms_found', {})
    
    # Build social media links section
    # Handle both formats:
    # - New format: platforms_found[platform] = {"present": true, "link": "...", "handle": "..."}
    # - Old format: platforms_found[platform] = true/false
    social_links = []
    for platform in ['facebook', 'instagram', 'tiktok', 'linkedin']:
        platform_data = platforms_found.get(platform)
        
        # Check if it's the new format (dict) or old format (bool)
        if isinstance(platform_data, dict):
            # New format: check for present and link
            if platform_data.get('present') and platform_data.get('link'):
                platform_name = platform.capitalize()
                if platform == 'linkedin':
                    platform_name = 'LinkedIn'
                elif platform == 'tiktok':
                    platform_name = 'TikTok'
                social_links.append(f"- **{platform_name}**: [{platform_data.get('handle', platform_data.get('link'))}]({platform_data.get('link')})")
        elif isinstance(platform_data, bool) and platform_data:
            # Old format: just a boolean, but we don't have the link
            # Skip it since we can't provide a link
            pass
    
    if social_links:
        data['social_links'] = '\n'.join(social_links)
    else:
        data['social_links'] = 'No social media links found.'
    
    return data


def generate_report(application_profile: Dict[str, Any], template: str, generation_date: str) -> str:
    """
    Generate a markdown report for an application.
    
    Args:
        application_profile: The application profile dictionary
        template: Template string with placeholders
        generation_date: Date string for report generation
        
    Returns:
        Formatted markdown report
    """
    data = extract_report_data(application_profile)
    data['generation_date'] = generation_date
    
    # Format the template with data
    try:
        report = template.format(**data)
    except KeyError as e:
        # If a key is missing, use 'N/A' as default
        missing_key = str(e).strip("'")
        data[missing_key] = 'N/A'
        report = template.format(**data)
    
    return report


def standardize_country_name(country: str) -> str:
    """
    Standardize country names to common format.
    Consolidates variations like USA, United States, United States of America.
    
    Args:
        country: Country name to standardize
        
    Returns:
        Standardized country name
    """
    if not country:
        return country
    
    country_lower = country.strip().lower()
    
    # Common country name mappings
    country_mappings = {
        # United States variations
        'usa': 'United States',
        'u.s.a.': 'United States',
        'u.s.a': 'United States',
        'us': 'United States',
        'u.s.': 'United States',
        'u.s': 'United States',
        'united states': 'United States',
        'united states of america': 'United States',
        'america': 'United States',
        
        # United Kingdom variations
        'uk': 'United Kingdom',
        'u.k.': 'United Kingdom',
        'u.k': 'United Kingdom',
        'united kingdom': 'United Kingdom',
        'great britain': 'United Kingdom',
        'britain': 'United Kingdom',
        'gb': 'United Kingdom',
        'g.b.': 'United Kingdom',
        
        # Canada
        'can': 'Canada',
        'ca': 'Canada',
        
        # Other common variations
        'south africa': 'South Africa',
        'southafrica': 'South Africa',
        'sa': 'South Africa',
        
        'australia': 'Australia',
        'aus': 'Australia',
        'oz': 'Australia',
        
        'new zealand': 'New Zealand',
        'nz': 'New Zealand',
        
        'mexico': 'Mexico',
        'mex': 'Mexico',
        
        'france': 'France',
        'french': 'France',
        
        'germany': 'Germany',
        'deutschland': 'Germany',
        'german': 'Germany',
        
        'italy': 'Italy',
        'italia': 'Italy',
        
        'spain': 'Spain',
        'españa': 'Spain',
        
        'netherlands': 'Netherlands',
        'the netherlands': 'Netherlands',
        'holland': 'Netherlands',
        
        'india': 'India',
        'bharat': 'India',
        
        'china': 'China',
        'peoples republic of china': 'China',
        'prc': 'China',
        "people's republic of china": 'China',
        
        'japan': 'Japan',
        'nippon': 'Japan',
        
        'brazil': 'Brazil',
        'brasil': 'Brazil',
        
        'argentina': 'Argentina',
        
        'chile': 'Chile',
        
        'colombia': 'Colombia',
        
        'philippines': 'Philippines',
        'phil': 'Philippines',
    }
    
    # Check for exact match (case-insensitive)
    if country_lower in country_mappings:
        return country_mappings[country_lower]
    
    # Check for partial matches (e.g., "United States of America" contains "united states")
    # Sort by key length (longest first) to match more specific variations first
    sorted_mappings = sorted(country_mappings.items(), key=lambda x: len(x[0]), reverse=True)
    for key, standard_name in sorted_mappings:
        # Check if the country contains the key or vice versa
        # Prefer matching longer keys to avoid false positives
        if key in country_lower:
            return standard_name
    
    # If no match found, return title-cased version of original
    # This handles cases where the country name is already in a reasonable format
    return country.strip().title()


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
    country_raw = home_address.get('country') or ''
    country_standardized = standardize_country_name(country_raw) if country_raw else ''
    
    # Clean email address (remove spaces)
    email_raw = profile.get('email') or ''
    email_cleaned = email_raw.replace(' ', '') if email_raw else ''
    
    data = {
        'first_name': profile.get('first_name') or '',
        'last_name': profile.get('last_name') or '',
        'email': email_cleaned,
        'wai_membership_number': profile.get('wai_membership_number') or '',
        'wai_application_number': profile.get('wai_application_number') or '',
        'country': country_standardized,
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


def process_single_application_step3(
    output_folder: str,
    template: str,
    generation_date: str,
    verbose: bool = True
) -> dict:
    """
    Generate a report for a single application.
    
    Args:
        output_folder: Path to the output folder containing application_profile.json
        template: Template string for the report
        generation_date: Date string for report generation
        verbose: Whether to print progress messages
        
    Returns:
        Dictionary with processing result
    """
    output_path = Path(output_folder)
    application_folder = output_path.name
    
    try:
        # Load application profile
        application_profile_file = output_path / "application_profile.json"
        if not application_profile_file.exists():
            error_msg = f"ERROR: application_profile.json not found in {output_folder}"
            if verbose:
                print(f"   {error_msg}")
            return {
                "success": False,
                "folder": application_folder,
                "error": error_msg
            }
        
        with open(application_profile_file, 'r', encoding='utf-8') as f:
            application_profile = json.load(f)
        
        # Generate report
        report = generate_report(application_profile, template, generation_date)
        
        # Save report
        report_file = output_path / "review_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        if verbose:
            total_score = application_profile.get('total_score_summary', {}).get('total_score', 0)
            print(f"   Generated report: {report_file.name} (Total score: {total_score})")
        
        return {
            "success": True,
            "folder": application_folder,
            "report_file": str(report_file),
            "application_profile": application_profile
        }
        
    except Exception as e:
        error_msg = f"ERROR: {str(e)}"
        if verbose:
            print(f"   {error_msg}")
        log_exception(e, "step3.py", f"process_single_application_step3: {application_folder}")
        return {
            "success": False,
            "folder": application_folder,
            "error": error_msg
        }


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate review board reports for applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate reports for all applications
  python code/step3.py
  
  # Generate reports for specific scholarship
  python code/step3.py --scholarship-folder "Delaney_Wings"
  
  # Use custom template
  python code/step3.py --template "templates/custom_report.md"
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
        help="Process applications from a specific scholarship folder only"
    )
    
    parser.add_argument(
        "--application-folder",
        type=str,
        default=None,
        help="Process a specific application folder only"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of applications to process (default: 0 = process all, use --limit N to limit to N applications)"
    )
    
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Path to custom report template file (default: uses built-in template)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
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
    
    verbose = not args.quiet
    
    # Load template
    template_path = Path(args.template) if args.template else None
    template = load_template(template_path)
    
    if verbose and args.template:
        print(f"Loaded custom template from: {args.template}")
    
    # Get generation date
    from datetime import datetime
    generation_date = datetime.now().strftime("%B %d, %Y")
    
    # Find scholarship folders
    scholarship_folders = []
    if args.scholarship_folder:
        scholarship_path = output_dir / args.scholarship_folder
        if scholarship_path.exists() and scholarship_path.is_dir():
            scholarship_folders = [(args.scholarship_folder, scholarship_path)]
        else:
            print(f"ERROR: Scholarship folder not found: {scholarship_path}")
            sys.exit(1)
    else:
        # Find all scholarship folders
        for item in output_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if this looks like a scholarship folder
                has_applications = False
                try:
                    for app_dir in item.iterdir():
                        if app_dir.is_dir() and not app_dir.name.startswith('.'):
                            if (app_dir / "application_profile.json").exists():
                                has_applications = True
                                break
                except Exception:
                    continue
                
                if has_applications:
                    scholarship_folders.append((item.name, item))
    
    if not scholarship_folders:
        print(f"ERROR: No scholarship folders found in {output_dir}")
        sys.exit(1)
    
    # Print summary
    if verbose:
        print("=" * 60)
        print("Step 3: Review Board Report Generation")
        print("=" * 60)
        print(f"Output directory: {output_dir}")
        print(f"Scholarship folders to process: {len(scholarship_folders)}")
        if args.limit and args.limit > 0:
            print(f"Limit: {args.limit} applications per scholarship")
        else:
            print(f"Limit: all (default)")
        print("=" * 60)
    
    # Step 1: Collect all application profiles and generate CSV first
    if verbose:
        print("\n" + "=" * 60)
        print("Step 1: Collecting Application Data and Generating CSV")
        print("=" * 60)
    
    all_applications_data = []
    
    for scholarship_name, scholarship_path in scholarship_folders:
        if verbose:
            print(f"\n  Collecting from scholarship: {scholarship_name}")
        
        # Find all application folders
        if args.application_folder:
            application_folders = [args.application_folder]
        else:
            application_folders = [
                item.name for item in scholarship_path.iterdir()
                if item.is_dir() 
                and not item.name.startswith('.')
                and (item / "application_profile.json").exists()
            ]
        
        if not application_folders:
            continue
        
        # Load all application profiles
        for app_folder in application_folders:
            folder_path = scholarship_path / app_folder
            profile_file = folder_path / "application_profile.json"
            
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    application_profile = json.load(f)
                
                all_applications_data.append({
                    'scholarship_folder': scholarship_name,
                    'application_folder': app_folder,
                    'folder_path': folder_path,
                    'profile': application_profile
                })
            except Exception as e:
                if verbose:
                    print(f"    WARNING: Could not load profile from {app_folder}: {e}")
                continue
    
    if not all_applications_data:
        print("ERROR: No application profiles found")
        sys.exit(1)
    
    if verbose:
        print(f"\n  Collected {len(all_applications_data)} application profile(s)")
    
    # Generate CSV file first
    if verbose:
        print("\n" + "=" * 60)
        print("Generating Summary Spreadsheet (CSV)")
        print("=" * 60)
    
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
    for app in all_applications_data:
        data = extract_applicant_data(app['profile'])
        data['scholarship_folder'] = app['scholarship_folder']
        data['application_folder'] = app['application_folder']
        rows.append(data)
    
    # Sort rows by total_score (highest first) for CSV
    def get_total_score(row):
        score = row.get('total_score', 0)
        if isinstance(score, (int, float)):
            return float(score)
        elif isinstance(score, str):
            try:
                return float(score)
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    rows.sort(key=get_total_score, reverse=True)
    
    # Group rows by scholarship folder and save CSV file per scholarship
    scholarship_rows = defaultdict(list)
    for row in rows:
        scholarship_folder = row.get('scholarship_folder', '')
        if scholarship_folder:
            scholarship_rows[scholarship_folder].append(row)
    
    # Save CSV files for each scholarship
    for scholarship_name, scholarship_data in scholarship_rows.items():
        # Create output subfolder for this scholarship
        scholarship_output_dir = output_dir / scholarship_name / "output"
        scholarship_output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_filename = "applicant_scores_summary.csv"
        csv_file = scholarship_output_dir / csv_filename
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(scholarship_data)
        
        if verbose:
            print(f"  Generated CSV for {scholarship_name}: {csv_file}")
            print(f"    Exported {len(scholarship_data)} applications")
    
    # Step 2: Determine which applicants to process based on CSV and --limit
    if args.limit and args.limit > 0:
        # Use CSV to identify top N applicants by total score (already sorted)
        if verbose:
            print(f"\n" + "=" * 60)
            print(f"Step 2: Selecting Top {args.limit} Applicants from CSV")
            print("=" * 60)
        
        # Create a set of top applicants (scholarship_folder, application_folder pairs)
        top_applicants = set()
        for scholarship_name, scholarship_data in scholarship_rows.items():
            top_for_scholarship = scholarship_data[:args.limit]
            for row in top_for_scholarship:
                top_applicants.add((row['scholarship_folder'], row['application_folder']))
        
        if verbose:
            print(f"  Selected {len(top_applicants)} top applicant(s) for report generation")
        
        # Filter all_applications_data to only include top applicants
        all_applications_data = [
            app for app in all_applications_data
            if (app['scholarship_folder'], app['application_folder']) in top_applicants
        ]
    
    # Step 3: Generate reports for selected applicants
    if verbose:
        print("\n" + "=" * 60)
        print("Step 3: Generating Review Board Reports")
        print("=" * 60)
    
    all_results = []
    total_successful = 0
    total_failed = 0
    
    # Group applications by scholarship for better output
    by_scholarship = defaultdict(list)
    for app in all_applications_data:
        by_scholarship[app['scholarship_folder']].append(app)
    
    for scholarship_name, scholarship_apps in by_scholarship.items():
        if verbose:
            print(f"\n  Processing scholarship: {scholarship_name} ({len(scholarship_apps)} application(s))")
        
        # Process each application folder
        for i, app in enumerate(scholarship_apps, 1):
            app_folder = app['application_folder']
            folder_path = app['folder_path']
            
            if verbose and len(scholarship_apps) > 1:
                print(f"    [{i}/{len(scholarship_apps)}] Processing: {app_folder}")
            
            result = process_single_application_step3(
                output_folder=str(folder_path),
                template=template,
                generation_date=generation_date,
                verbose=verbose and len(scholarship_apps) <= 10  # Only verbose if <= 10 apps
            )
            
            # Add scholarship folder name to result
            result["scholarship_folder"] = scholarship_name
            all_results.append(result)
            if result["success"]:
                total_successful += 1
            else:
                total_failed += 1
                if verbose:
                    print(f"    ERROR: {result.get('error', 'Unknown error')}")
    
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
    
    log_summary("step3.py", summary)
    
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    try:
        # Parse arguments first to get script name and args for logging
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--scholarship-folder", type=str, default=None)
        parser.add_argument("--application-folder", type=str, default=None)
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--template", type=str, default=None)
        parser.add_argument("--output-dir", type=str, default=None)
        parser.add_argument("--quiet", action="store_true")
        
        # Parse known args only (don't error on unknown)
        args, _ = parser.parse_known_args()
        
        # Prepare args dict for logging
        log_args = {
            "scholarship_folder": args.scholarship_folder,
            "application_folder": args.application_folder,
            "limit": args.limit if (args.limit and args.limit > 0) else "all",
            "template": args.template,
            "output_dir": args.output_dir,
            "quiet": args.quiet
        }
        
        # Use execution logger
        with execution_logger("step3.py", log_args):
            main()
    except Exception as e:
        log_exception(e, "step3.py", "main execution")
        raise

