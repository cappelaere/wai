#!/usr/bin/env python3
"""
Step 5: Generate Scholarship Statistics Report

This script gathers statistics on a particular scholarship and generates
a comprehensive markdown report including:
- Number of applicants
- Score statistics and percentiles
- Geographic distribution (countries and states)
- Score breakdowns by agent
- Other relevant metrics
"""

import os
import sys
import json
import argparse
import statistics
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter, defaultdict
from dotenv import load_dotenv

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:
    print("WARNING: reportlab not installed. PDF generation will be disabled.")
    print("To enable PDF generation, install reportlab: pip install reportlab")
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True

# Load environment variables
load_dotenv()

# Import logging utilities
from processor.utils.logging_utils import execution_logger, log_exception, log_summary


def load_template(template_path: Optional[Path] = None) -> str:
    """
    Load the statistics report template.
    
    Args:
        template_path: Optional path to custom template file
        
    Returns:
        Template string
    """
    if template_path and template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Default template path
    default_template = Path(__file__).parent / "templates" / "scholarship_statistics_template.md"
    if default_template.exists():
        with open(default_template, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Fallback: return error message
    return f"Error: Template Not Found\nTemplate path: {template_path or default_template}"


def find_application_folders(output_dir: Path, scholarship_folder: str) -> List[Path]:
    """
    Find all application folders for a specific scholarship.
    
    Args:
        output_dir: Base output directory
        scholarship_folder: Scholarship folder name
        
    Returns:
        List of application folder paths
    """
    applications = []
    scholarship_path = output_dir / scholarship_folder
    
    if not scholarship_path.exists() or not scholarship_path.is_dir():
        return applications
    
    for app_dir in scholarship_path.iterdir():
        if app_dir.is_dir() and not app_dir.name.startswith('.'):
            profile_file = app_dir / "application_profile.json"
            if profile_file.exists():
                applications.append(app_dir)
    
    # Sort numerically if possible
    def sort_key(path):
        name = path.name
        try:
            return int(name)
        except ValueError:
            return name
    
    applications.sort(key=sort_key)
    return applications


def load_application_profile(app_dir: Path) -> Optional[Dict[str, Any]]:
    """Load application profile from JSON file."""
    profile_file = app_dir / "application_profile.json"
    if not profile_file.exists():
        return None
    
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load profile from {app_dir.name}: {e}")
        return None


def extract_statistics(applications: List[Path], verbose: bool = True) -> Dict[str, Any]:
    """
    Extract statistics from all application profiles.
    
    Args:
        applications: List of application folder paths
        verbose: Whether to print progress
        
    Returns:
        Dictionary with all statistics
    """
    stats = {
        'total_applicants': len(applications),
        'total_scores': [],
        'application_scores': [],
        'personal_scores': [],
        'recommendation_scores': [],
        'academic_scores': [],
        'social_scores': [],
        'countries': Counter(),
        'states': Counter(),
        'cities': Counter(),
        'completeness': {
            'has_resume': 0,
            'has_essay': 0,
            'has_recommendations': 0,
            'num_recommendations': [],
            'has_medical_certificate': 0,
            'has_logbook': 0
        },
        'aviation_path_stages': Counter(),
        'total_platforms_count': []
    }
    
    if verbose:
        print(f"Extracting statistics from {len(applications)} applications...")
    
    for i, app_dir in enumerate(applications, 1):
        if verbose and i % 10 == 0:
            print(f"  Processing application {i}/{len(applications)}...")
        
        profile = load_application_profile(app_dir)
        if not profile:
            continue
        
        # Extract total score
        total_score_summary = profile.get('total_score_summary', {})
        total_score = total_score_summary.get('total_score', 0)
        if isinstance(total_score, (int, float)):
            stats['total_scores'].append(float(total_score))
        elif isinstance(total_score, str):
            try:
                stats['total_scores'].append(float(total_score))
            except (ValueError, TypeError):
                pass
        
        # Extract profile data
        profile_data = profile.get('profile', {})
        home_address = profile_data.get('home_address', {})
        
        # Geographic data
        country_raw = home_address.get('country', '').strip()
        country = None
        if country_raw:
            # Standardize country name once
            country = standardize_country_name(country_raw)
            stats['countries'][country] += 1
        
        state_province_raw = home_address.get('state_province', '').strip()
        if state_province_raw:
            # Standardize state/province name (for US states, use two-letter codes)
            state_province_std = standardize_state_name(state_province_raw, country)
            # Combine with standardized country for better context
            if country:
                stats['states'][f"{state_province_std}, {country}"] += 1
            else:
                stats['states'][state_province_std] += 1
        
        city = home_address.get('city', '').strip()
        if city and country:
            # Use standardized country name for cities
            stats['cities'][f"{city}, {country}"] += 1
        
        # Extract scores by agent
        # Application scores
        app_scores = profile.get('scores', {})
        app_score = app_scores.get('overall_score', 0)
        if isinstance(app_score, (int, float)):
            stats['application_scores'].append(float(app_score))
        
        # Personal scores
        personal_profile = profile.get('personal_profile', {})
        personal_scores = personal_profile.get('scores', {})
        personal_score = personal_scores.get('overall_score', 0)
        if isinstance(personal_score, (int, float)):
            stats['personal_scores'].append(float(personal_score))
        
        # Get aviation path stage
        profile_features = personal_profile.get('profile_features', {})
        aviation_path_stage = profile_features.get('aviation_path_stage', '')
        if aviation_path_stage:
            stats['aviation_path_stages'][aviation_path_stage] += 1
        
        # Recommendation scores
        recommendation_profile = profile.get('recommendation_profile', {})
        recommendation_scores = recommendation_profile.get('scores', {})
        recommendation_score = recommendation_scores.get('overall_score', 0)
        if isinstance(recommendation_score, (int, float)):
            stats['recommendation_scores'].append(float(recommendation_score))
        
        # Academic scores
        academic_profile = profile.get('academic_profile', {})
        academic_scores = academic_profile.get('scores', {})
        academic_score = academic_scores.get('overall_score', 0)
        if isinstance(academic_score, (int, float)):
            stats['academic_scores'].append(float(academic_score))
        
        # Social scores
        social_profile = profile.get('social_profile', {})
        social_scores = social_profile.get('scores', {})
        social_score = social_scores.get('overall_score', 0)
        if isinstance(social_score, (int, float)):
            stats['social_scores'].append(float(social_score))
        
        # Social media platforms
        social_features = social_profile.get('profile_features', {})
        total_platforms = social_features.get('total_platforms', 0)
        if isinstance(total_platforms, (int, float)):
            stats['total_platforms_count'].append(int(total_platforms))
        
        # Completeness metrics
        completeness = profile_data.get('completeness', {})
        if completeness.get('has_resume'):
            stats['completeness']['has_resume'] += 1
        if completeness.get('has_essay'):
            stats['completeness']['has_essay'] += 1
        num_recs = completeness.get('num_recommendation_letters', 0)
        if num_recs > 0:
            stats['completeness']['has_recommendations'] += 1
            stats['completeness']['num_recommendations'].append(num_recs)
        if completeness.get('has_medical_certificate'):
            stats['completeness']['has_medical_certificate'] += 1
        if completeness.get('has_logbook'):
            stats['completeness']['has_logbook'] += 1
    
    return stats


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


def standardize_state_name(state_province: str, country: Optional[str] = None) -> str:
    """
    Standardize state/province names to common format.
    For United States, uses two-letter postal codes.
    For other countries, standardizes common variations.
    
    Args:
        state_province: State or province name to standardize
        country: Optional country name (already standardized) for context
        
    Returns:
        Standardized state/province name
    """
    if not state_province:
        return state_province
    
    state_lower = state_province.strip().lower()
    
    # US State mappings to two-letter codes
    us_state_mappings = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'calif': 'CA', 'cali': 'CA',
        'colorado': 'CO', 'col': 'CO',
        'connecticut': 'CT', 'conn': 'CT',
        'delaware': 'DE',
        'florida': 'FL', 'fla': 'FL',
        'georgia': 'GA',
        'hawaii': 'HI',
        'idaho': 'ID',
        'illinois': 'IL', 'ill': 'IL',
        'indiana': 'IN', 'ind': 'IN',
        'iowa': 'IA',
        'kansas': 'KS', 'kan': 'KS',
        'kentucky': 'KY', 'ken': 'KY',
        'louisiana': 'LA',
        'maine': 'ME',
        'maryland': 'MD',
        'massachusetts': 'MA', 'mass': 'MA',
        'michigan': 'MI', 'mich': 'MI',
        'minnesota': 'MN', 'minn': 'MN',
        'mississippi': 'MS',
        'missouri': 'MO',
        'montana': 'MT',
        'nebraska': 'NE', 'neb': 'NE',
        'nevada': 'NV',
        'new hampshire': 'NH',
        'new jersey': 'NJ',
        'new mexico': 'NM',
        'new york': 'NY',
        'north carolina': 'NC', 'n.c.': 'NC', 'nc': 'NC',
        'north dakota': 'ND', 'n.d.': 'ND', 'nd': 'ND',
        'ohio': 'OH',
        'oklahoma': 'OK', 'okla': 'OK',
        'oregon': 'OR', 'ore': 'OR',
        'pennsylvania': 'PA', 'penn': 'PA', 'penna': 'PA',
        'rhode island': 'RI', 'r.i.': 'RI',
        'south carolina': 'SC', 's.c.': 'SC', 'sc': 'SC',
        'south dakota': 'SD', 's.d.': 'SD', 'sd': 'SD',
        'tennessee': 'TN', 'tenn': 'TN',
        'texas': 'TX', 'tex': 'TX',
        'utah': 'UT',
        'vermont': 'VT',
        'virginia': 'VA',
        'washington': 'WA', 'wash': 'WA',
        'west virginia': 'WV', 'w.va.': 'WV', 'wva': 'WV',
        'wisconsin': 'WI', 'wis': 'WI',
        'wyoming': 'WY', 'wyo': 'WY',
        # Also handle already-standardized codes
        'al': 'AL', 'ak': 'AK', 'az': 'AZ', 'ar': 'AR',
        'ca': 'CA', 'co': 'CO', 'ct': 'CT', 'de': 'DE',
        'fl': 'FL', 'ga': 'GA', 'hi': 'HI', 'id': 'ID',
        'il': 'IL', 'in': 'IN', 'ia': 'IA', 'ks': 'KS',
        'ky': 'KY', 'la': 'LA', 'me': 'ME', 'md': 'MD',
        'ma': 'MA', 'mi': 'MI', 'mn': 'MN', 'ms': 'MS',
        'mo': 'MO', 'mt': 'MT', 'ne': 'NE', 'nv': 'NV',
        'nh': 'NH', 'nj': 'NJ', 'nm': 'NM', 'ny': 'NY',
        'oh': 'OH', 'ok': 'OK', 'or': 'OR', 'pa': 'PA',
        'ri': 'RI', 'sc': 'SC', 'sd': 'SD', 'tn': 'TN',
        'tx': 'TX', 'ut': 'UT', 'vt': 'VT', 'va': 'VA',
        'wa': 'WA', 'wv': 'WV', 'wi': 'WI', 'wy': 'WY',
        # DC
        'district of columbia': 'DC', 'd.c.': 'DC', 'dc': 'DC',
        # Territories
        'puerto rico': 'PR', 'pr': 'PR',
        'american samoa': 'AS', 'as': 'AS',
        'guam': 'GU', 'gu': 'GU',
        'u.s. virgin islands': 'VI', 'virgin islands': 'VI', 'vi': 'VI',
        'northern mariana islands': 'MP', 'mp': 'MP',
    }
    
    # If country is United States, use US state mappings
    if country and country.lower() in ['united states', 'usa', 'us', 'u.s.', 'u.s', 'america']:
        # Check for exact match
        if state_lower in us_state_mappings:
            return us_state_mappings[state_lower]
        
        # Check for partial matches (e.g., "New York State" contains "new york")
        sorted_mappings = sorted(us_state_mappings.items(), key=lambda x: len(x[0]), reverse=True)
        for key, code in sorted_mappings:
            if key in state_lower:
                return code
    
    # For other countries, standardize common province/state variations
    if country:
        country_lower = country.lower()
        
        # Canada provinces
        if country_lower == 'canada':
            canada_mappings = {
                'alberta': 'AB', 'ab': 'AB', 'alta': 'AB',
                'british columbia': 'BC', 'bc': 'BC', 'b.c.': 'BC',
                'manitoba': 'MB', 'mb': 'MB', 'man': 'MB',
                'new brunswick': 'NB', 'nb': 'NB', 'n.b.': 'NB',
                'newfoundland and labrador': 'NL', 'nl': 'NL', 'nfld': 'NL',
                'northwest territories': 'NT', 'nt': 'NT', 'n.w.t.': 'NT',
                'nova scotia': 'NS', 'ns': 'NS', 'n.s.': 'NS',
                'nunavut': 'NU', 'nu': 'NU',
                'ontario': 'ON', 'on': 'ON', 'ont': 'ON',
                'prince edward island': 'PE', 'pe': 'PE', 'p.e.i.': 'PE',
                'quebec': 'QC', 'qc': 'QC', 'québec': 'QC', 'pq': 'QC', 'p.q.': 'QC',
                'saskatchewan': 'SK', 'sk': 'SK', 'sask': 'SK',
                'yukon': 'YT', 'yt': 'YT', 'yukon territory': 'YT',
            }
            if state_lower in canada_mappings:
                return canada_mappings[state_lower]
            # Check partial matches
            sorted_canada = sorted(canada_mappings.items(), key=lambda x: len(x[0]), reverse=True)
            for key, code_val in sorted_canada:
                if key in state_lower:
                    return code_val
        
        # Australia states/territories
        elif country_lower == 'australia':
            australia_mappings = {
                'new south wales': 'NSW', 'nsw': 'NSW',
                'victoria': 'VIC', 'vic': 'VIC',
                'queensland': 'QLD', 'qld': 'QLD',
                'western australia': 'WA', 'wa': 'WA',
                'south australia': 'SA', 'sa': 'SA',
                'tasmania': 'TAS', 'tas': 'TAS',
                'northern territory': 'NT', 'nt': 'NT',
                'australian capital territory': 'ACT', 'act': 'ACT',
            }
            if state_lower in australia_mappings:
                return australia_mappings[state_lower]
            sorted_aus = sorted(australia_mappings.items(), key=lambda x: len(x[0]), reverse=True)
            for key, code_val in sorted_aus:
                if key in state_lower:
                    return code_val
    
    # If no specific mapping found, return title-cased version
    return state_province.strip().title()


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile of a list of numbers."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    if index.is_integer():
        return sorted_data[int(index)]
    else:
        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def format_statistics(stats: Dict[str, Any], scholarship_name: str, generation_date: str) -> Dict[str, str]:
    """
    Format statistics for template substitution.
    
    Args:
        stats: Statistics dictionary
        scholarship_name: Name of the scholarship
        generation_date: Date string
        
    Returns:
        Dictionary with formatted values for template
    """
    total_scores = stats['total_scores']
    
    def safe_stat(func, data, default=0.0):
        """Safely calculate statistics, returning default if data is empty."""
        if not data:
            return default
        try:
            return func(data)
        except:
            return default
    
    # Total score statistics
    min_total = safe_stat(min, total_scores)
    max_total = safe_stat(max, total_scores)
    mean_total = safe_stat(statistics.mean, total_scores)
    median_total = safe_stat(statistics.median, total_scores)
    std_dev_total = safe_stat(statistics.stdev, total_scores) if len(total_scores) > 1 else 0.0
    
    # Percentiles
    p25 = calculate_percentile(total_scores, 25)
    p50 = calculate_percentile(total_scores, 50)
    p75 = calculate_percentile(total_scores, 75)
    p90 = calculate_percentile(total_scores, 90)
    p95 = calculate_percentile(total_scores, 95)
    p99 = calculate_percentile(total_scores, 99)
    
    # Score distribution based on percentiles
    score_dist_lines = []
    if total_scores:
        # Calculate percentile boundaries
        percentile_boundaries = {
            0: min_total,
            25: p25,
            50: p50,
            75: p75,
            90: p90,
            95: p95,
            100: max_total
        }
        
        # Define percentile ranges with labels
        percentile_ranges = [
            (0, 25, "Bottom Quartile (0-25th percentile)"),
            (25, 50, "Second Quartile (25th-50th percentile)"),
            (50, 75, "Third Quartile (50th-75th percentile)"),
            (75, 90, "75th-90th percentile"),
            (90, 95, "90th-95th percentile"),
            (95, 100, "Top 5% (95th-100th percentile)")
        ]
        
        # Sort scores to calculate percentile positions accurately
        sorted_scores = sorted(total_scores)
        n = len(sorted_scores)
        
        # Count scores in each percentile range based on actual position in sorted list
        for lower_pct, upper_pct, label in percentile_ranges:
            # Calculate the index range for this percentile using same method as calculate_percentile
            lower_idx = int((lower_pct / 100) * (n - 1))
            if upper_pct == 100:
                upper_idx = n - 1  # Last index (inclusive)
            else:
                upper_idx = int((upper_pct / 100) * (n - 1))
            
            # Get the actual score boundaries for display
            lower_bound = percentile_boundaries[lower_pct]
            upper_bound = percentile_boundaries[upper_pct]
            
            # Count scores by their position in the sorted list
            # This ensures each score is counted exactly once in the appropriate percentile range
            if upper_pct == 100:
                # Last range: from lower_idx to end (inclusive)
                count = n - lower_idx
            else:
                # Other ranges: from lower_idx to upper_idx (inclusive)
                count = upper_idx - lower_idx + 1
            
            percentage = (count / len(total_scores) * 100) if total_scores else 0
            score_dist_lines.append(f"- **{label}** ({lower_bound:.1f} - {upper_bound:.1f}): {count} applicants ({percentage:.1f}%)")
        
        score_distribution = '\n'.join(score_dist_lines)
    else:
        score_distribution = "No score data available."
    
    # Countries list
    countries_list_lines = []
    for country, count in stats['countries'].most_common():
        percentage = (count / stats['total_applicants'] * 100) if stats['total_applicants'] > 0 else 0
        countries_list_lines.append(f"- **{country}:** {count} ({percentage:.1f}%)")
    countries_list = '\n'.join(countries_list_lines) if countries_list_lines else "No countries found"
    
    # States list - only US states
    us_states = {}
    for state_key, count in stats['states'].items():
        # Check if this is a US state (format: "ST, United States" or just state code)
        if ', United States' in state_key:
            # Extract state code (e.g., "CA, United States" -> "CA")
            state_code = state_key.split(',')[0].strip()
            us_states[state_code] = us_states.get(state_code, 0) + count
        elif state_key.upper() in ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'PR', 'AS', 'GU', 'VI', 'MP']:
            # Standalone US state code
            us_states[state_key.upper()] = us_states.get(state_key.upper(), 0) + count
    
    states_list_lines = []
    # Sort by count (highest first), then by state code
    sorted_us_states = sorted(us_states.items(), key=lambda x: (-x[1], x[0]))
    for state_code, count in sorted_us_states:
        percentage = (count / stats['total_applicants'] * 100) if stats['total_applicants'] > 0 else 0
        states_list_lines.append(f"- **{state_code}:** {count} ({percentage:.1f}%)")
    
    states_list = '\n'.join(states_list_lines) if states_list_lines else "No US states found"
    total_us_states = len(us_states)
    
    # Agent score statistics
    agent_scores = {
        'application': stats['application_scores'],
        'personal': stats['personal_scores'],
        'recommendation': stats['recommendation_scores'],
        'academic': stats['academic_scores'],
        'social': stats['social_scores']
    }
    
    agent_stats = {}
    for agent_name, scores in agent_scores.items():
        agent_stats[f'min_{agent_name}_score'] = safe_stat(min, scores)
        agent_stats[f'max_{agent_name}_score'] = safe_stat(max, scores)
        agent_stats[f'mean_{agent_name}_score'] = safe_stat(statistics.mean, scores)
        agent_stats[f'median_{agent_name}_score'] = safe_stat(statistics.median, scores)
    
    # Completeness metrics
    completeness = stats['completeness']
    total = stats['total_applicants']
    completeness_lines = [
        f"- **Resume:** {completeness['has_resume']}/{total} ({completeness['has_resume']/total*100:.1f}%)" if total > 0 else "- **Resume:** 0/0 (0.0%)",
        f"- **Essay:** {completeness['has_essay']}/{total} ({completeness['has_essay']/total*100:.1f}%)" if total > 0 else "- **Essay:** 0/0 (0.0%)",
        f"- **Recommendations:** {completeness['has_recommendations']}/{total} ({completeness['has_recommendations']/total*100:.1f}%)" if total > 0 else "- **Recommendations:** 0/0 (0.0%)",
    ]
    if completeness['num_recommendations']:
        avg_recs = safe_stat(statistics.mean, completeness['num_recommendations'])
        completeness_lines.append(f"- **Average Number of Recommendations:** {avg_recs:.1f}")
    completeness_lines.extend([
        f"- **Medical Certificate:** {completeness['has_medical_certificate']}/{total} ({completeness['has_medical_certificate']/total*100:.1f}%)" if total > 0 else "- **Medical Certificate:** 0/0 (0.0%)",
        f"- **Flight Log:** {completeness['has_logbook']}/{total} ({completeness['has_logbook']/total*100:.1f}%)" if total > 0 else "- **Flight Log:** 0/0 (0.0%)"
    ])
    completeness_metrics = '\n'.join(completeness_lines)
    
    # Additional statistics
    additional_lines = []
    
    # Count zero-score applications (outliers)
    zero_score_count = sum(1 for score in total_scores if score == 0.0 or score == 0)
    zero_score_percentage = (zero_score_count / total * 100) if total > 0 else 0.0
    
    # Add to additional statistics if there are any zero scores
    if zero_score_count > 0:
        additional_lines.append("### Outliers")
        additional_lines.append(f"- **Applications with Zero Score:** {zero_score_count} ({zero_score_percentage:.1f}%)")
        additional_lines.append(f"  These applications may require manual review or have missing/incomplete data.")
        additional_lines.append("")
    
    # Aviation path stages
    if stats['aviation_path_stages']:
        additional_lines.append("### Aviation Path Stages")
        for stage, count in stats['aviation_path_stages'].most_common():
            percentage = (count / total * 100) if total > 0 else 0
            additional_lines.append(f"- **{stage.replace('_', ' ').title()}:** {count} ({percentage:.1f}%)")
        additional_lines.append("")
    
    # Social media presence
    if stats['total_platforms_count']:
        avg_platforms = safe_stat(statistics.mean, stats['total_platforms_count'])
        max_platforms = safe_stat(max, stats['total_platforms_count'])
        additional_lines.append("### Social Media Presence")
        additional_lines.append(f"- **Average Platforms per Applicant:** {avg_platforms:.1f}")
        additional_lines.append(f"- **Maximum Platforms:** {max_platforms}")
        additional_lines.append("")
    
    # Top cities
    if stats['cities']:
        additional_lines.append("### Top Cities")
        for city, count in stats['cities'].most_common(10):
            percentage = (count / total * 100) if total > 0 else 0
            additional_lines.append(f"- **{city}:** {count} ({percentage:.1f}%)")
    
    additional_statistics = '\n'.join(additional_lines) if additional_lines else "No additional statistics available."
    
    return {
        'scholarship_name': scholarship_name,
        'generation_date': generation_date,
        'total_applicants': stats['total_applicants'],
        'zero_score_count': zero_score_count,
        'zero_score_percentage': zero_score_percentage,
        'min_total_score': min_total,
        'max_total_score': max_total,
        'mean_total_score': mean_total,
        'median_total_score': median_total,
        'std_dev_total_score': std_dev_total,
        'p25_total_score': p25,
        'p50_total_score': p50,
        'p75_total_score': p75,
        'p90_total_score': p90,
        'p95_total_score': p95,
        'p99_total_score': p99,
        'score_distribution': score_distribution,
        'total_countries': len(stats['countries']),
        'countries_list': countries_list,
        'total_states': total_us_states,
        'states_list': states_list,
        'completeness_metrics': completeness_metrics,
        'additional_statistics': additional_statistics,
        **agent_stats
    }


def generate_report(stats_data: Dict[str, str], template: str) -> str:
    """Generate markdown report from template and statistics."""
    return template.format(**stats_data)


def escape_xml(text: str) -> str:
    """Escape XML special characters for reportlab Paragraph."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))


def markdown_to_reportlab_elements(markdown_content: str) -> List:
    """
    Convert markdown content to reportlab elements.
    
    Args:
        markdown_content: Markdown content as string
        
    Returns:
        List of reportlab elements (Paragraph, Spacer, PageBreak, etc.)
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Cannot generate PDF.")
    
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        borderWidth=0,
        borderPadding=0,
        borderColor=HexColor('#3498db'),
        backColor=HexColor('#ffffff')
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=16
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#555555'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    elements = []
    lines = markdown_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines (but add small spacer)
        if not line:
            elements.append(Spacer(1, 6))
            i += 1
            continue
        
        # Check for page break marker
        if line == '<!-- PAGE_BREAK -->':
            elements.append(PageBreak())
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            text = escape_xml(line[2:].strip())
            elements.append(Paragraph(text, h1_style))
            elements.append(Spacer(1, 6))
        elif line.startswith('## '):
            text = escape_xml(line[3:].strip())
            elements.append(Paragraph(text, h2_style))
            elements.append(Spacer(1, 4))
        elif line.startswith('### '):
            text = escape_xml(line[4:].strip())
            elements.append(Paragraph(text, h3_style))
            elements.append(Spacer(1, 4))
        # Horizontal rule
        elif line.startswith('---') or line.startswith('***'):
            elements.append(Spacer(1, 12))
            # Simple line representation
            elements.append(Paragraph('<font color="#ecf0f1">_________________________________________________________________</font>', normal_style))
            elements.append(Spacer(1, 12))
        # List items
        elif line.startswith('- ') or line.startswith('* '):
            text = escape_xml(line[2:].strip())
            # Convert markdown bold/italic to reportlab format
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            elements.append(Paragraph(f'&bull; {text}', normal_style))
        # Regular paragraph
        else:
            text = escape_xml(line)
            # Convert markdown bold/italic to reportlab format
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            # Convert markdown links [text](url) to reportlab format
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<u color="#3498db">\1</u>', text)
            elements.append(Paragraph(text, normal_style))
        
        i += 1
    
    return elements


def markdown_to_pdf(markdown_content: str, output_pdf_path: Path, verbose: bool = True) -> bool:
    """
    Convert markdown content to PDF using reportlab.
    
    Args:
        markdown_content: Markdown content as string
        output_pdf_path: Path where PDF should be saved
        verbose: Whether to print progress
        
    Returns:
        True if successful, False otherwise
    """
    if not REPORTLAB_AVAILABLE:
        if verbose:
            print("  ERROR: reportlab is not installed. Cannot generate PDF.")
            print("  Install it with: pip install reportlab")
        return False
    
    try:
        if verbose:
            print(f"  Generating PDF: {output_pdf_path.name}...")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_pdf_path),
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Convert markdown to reportlab elements
        elements = markdown_to_reportlab_elements(markdown_content)
        
        # Build PDF
        doc.build(elements)
        
        if verbose:
            file_size = output_pdf_path.stat().st_size / 1024  # Size in KB
            print(f"  PDF generated successfully ({file_size:.1f} KB)")
        
        return True
    except Exception as e:
        if verbose:
            print(f"  ERROR: Failed to generate PDF: {str(e)}")
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Step 5: Generate Scholarship Statistics Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate statistics report for a scholarship
  python code/step5.py --scholarship-folder "Delaney_Wings"

  # Generate report with custom output filename
  python code/step5.py --scholarship-folder "Delaney_Wings" --output "delaney_statistics.md"

  # Use custom template
  python code/step5.py --scholarship-folder "Delaney_Wings" --template "templates/custom_stats.md"

  # Generate markdown only (no PDF)
  python code/step5.py --scholarship-folder "Delaney_Wings" --markdown-only
        """
    )
    
    parser.add_argument(
        "--scholarship-folder",
        type=str,
        required=True,
        help="Scholarship folder name (e.g., 'Delaney_Wings')"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base output directory containing application profiles (default: from OUTPUT_DATA_DIR env var or 'output')"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output markdown filename (default: 'statistics_report.md' in {scholarship_folder}/output/). PDF will be saved with .pdf extension."
    )
    
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Path to custom statistics template file (default: uses built-in template)"
    )
    
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="Only generate markdown file, do not create PDF"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output (only show errors and summary)"
    )
    
    args = parser.parse_args()
    
    # Get configuration from arguments or environment variables
    base_output_dir = Path(os.getenv("OUTPUT_DATA_DIR", "output"))
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = base_output_dir
    
    verbose = not args.quiet
    
    if not output_dir.exists():
        print(f"ERROR: Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    if not output_dir.is_dir():
        print(f"ERROR: Path is not a directory: {output_dir}")
        sys.exit(1)
    
    if verbose:
        print("=" * 60)
        print("Step 5: Generate Scholarship Statistics Report")
        print("=" * 60)
        print(f"Output directory: {output_dir}")
        print(f"Scholarship folder: {args.scholarship_folder}")
        print("=" * 60)
    
    # Load template
    template_path = Path(args.template) if args.template else None
    template = load_template(template_path)
    if "Error: Template Not Found" in template:
        print(template)
        sys.exit(1)
    
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Find all application folders
    if verbose:
        print("\nFinding application folders...")
    
    applications = find_application_folders(output_dir, args.scholarship_folder)
    
    if not applications:
        print(f"ERROR: No application folders with application_profile.json found for scholarship '{args.scholarship_folder}' in {output_dir}")
        sys.exit(1)
    
    if verbose:
        print(f"Found {len(applications)} application(s)\n")
    
    # Extract statistics
    if verbose:
        print("Extracting statistics...")
    
    stats = extract_statistics(applications, verbose)
    
    if verbose:
        print(f"\nStatistics extracted:")
        print(f"  Total applicants: {stats['total_applicants']}")
        print(f"  Countries: {len(stats['countries'])}")
        # Count US states only
        us_states_count = sum(1 for state_key in stats['states'] if ', United States' in state_key or state_key.upper() in ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'PR', 'AS', 'GU', 'VI', 'MP'])
        print(f"  US States: {us_states_count}")
    
    # Format statistics for template
    stats_data = format_statistics(stats, args.scholarship_folder, generation_date)
    
    # Generate report
    if verbose:
        print("\nGenerating report...")
    
    report = generate_report(stats_data, template)
    
    # Determine output file path
    # Save to output subfolder within scholarship folder
    scholarship_output_dir = output_dir / args.scholarship_folder / "output"
    scholarship_output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.output:
        output_file = Path(args.output)
        # If output is a relative path, put it in the scholarship output directory
        if not output_file.is_absolute():
            output_file = scholarship_output_dir / output_file.name
    else:
        output_file = scholarship_output_dir / "statistics_report.md"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save markdown report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    if verbose:
        print(f"\nMarkdown report saved to: {output_file}")
    
    # Generate PDF if not markdown-only
    if not args.markdown_only:
        pdf_output_file = output_file.with_suffix('.pdf')
        if markdown_to_pdf(report, pdf_output_file, verbose):
            if verbose:
                print(f"PDF report saved to: {pdf_output_file}")
        else:
            if verbose:
                print("  PDF generation failed. Markdown report is still available.")
    
    if verbose:
        print("=" * 60)
    
    # Log summary
    summary = {
        "scholarship_folder": args.scholarship_folder,
        "total_applicants": stats['total_applicants'],
        "countries": len(stats['countries']),
        "us_states": len([s for s in stats['states'] if ', United States' in s or s.upper() in ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'PR', 'AS', 'GU', 'VI', 'MP']]),
        "output_file": str(output_file),
        "pdf_generated": not args.markdown_only and REPORTLAB_AVAILABLE
    }
    
    log_summary("step5.py", summary)


if __name__ == "__main__":
    try:
        # Parse arguments first to get script name and args for logging
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--scholarship-folder", type=str, default=None)
        parser.add_argument("--output-dir", type=str, default=None)
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--template", type=str, default=None)
        parser.add_argument("--quiet", action="store_true")
        
        # Parse known args only (don't error on unknown)
        args, _ = parser.parse_known_args()
        
        # Prepare args dict for logging
        log_args = {
            "scholarship_folder": args.scholarship_folder,
            "output_dir": args.output_dir,
            "output": args.output,
            "template": args.template,
            "quiet": args.quiet
        }
        
        # Use execution logger
        with execution_logger("step5.py", log_args):
            main()
    except Exception as e:
        log_exception(e, "step5.py", "main execution")
        raise

