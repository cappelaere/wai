#!/usr/bin/env python3
"""
Step 4: Combine Review Reports and Generate PDF

This script:
1. Finds all review_report.md files from Step 3
2. Combines them into a single markdown document
3. Converts the combined markdown to PDF using reportlab
4. Saves the PDF to the output directory
"""

import os
import sys
import argparse
import re
import json
import csv
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Import functions from step3 to generate individual reports
# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from step3 import load_template, extract_report_data, generate_report

# Import logging utilities
from logging_utils import execution_logger, log_exception, log_summary

# Load environment variables
load_dotenv()

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
    print("ERROR: Required libraries not installed.")
    print("Please install required dependencies:")
    print("  pip install reportlab")
    print(f"\nMissing: {e}")
    sys.exit(1)


def find_application_folders(output_dir: Path, scholarship_folder: Optional[str] = None) -> List[tuple]:
    """
    Find all application folders that have application_profile.json.
    
    Args:
        output_dir: Base output directory
        scholarship_folder: Optional scholarship folder to limit search
        
    Returns:
        List of tuples: (scholarship_name, application_folder_path, report_file_path)
    """
    applications = []
    
    if scholarship_folder:
        scholarship_path = output_dir / scholarship_folder
        if scholarship_path.exists() and scholarship_path.is_dir():
            for app_dir in scholarship_path.iterdir():
                if app_dir.is_dir() and not app_dir.name.startswith('.'):
                    profile_file = app_dir / "application_profile.json"
                    if profile_file.exists():
                        report_file = app_dir / "review_report.md"
                        applications.append((scholarship_folder, app_dir, report_file))
        else:
            print(f"ERROR: Scholarship folder not found: {scholarship_path}")
            return []
    else:
        # Search all scholarship folders
        for scholarship_dir in output_dir.iterdir():
            if scholarship_dir.is_dir() and not scholarship_dir.name.startswith('.'):
                scholarship_name = scholarship_dir.name
                for app_dir in scholarship_dir.iterdir():
                    if app_dir.is_dir() and not app_dir.name.startswith('.'):
                        profile_file = app_dir / "application_profile.json"
                        if profile_file.exists():
                            report_file = app_dir / "review_report.md"
                            applications.append((scholarship_name, app_dir, report_file))
    
    # Sort by scholarship folder and application folder (numeric sorting for app folders)
    def sort_key(item):
        scholarship_name, app_dir, _ = item
        app_folder = app_dir.name
        
        # Numeric sort for application folders
        if app_folder.isdigit():
            return (scholarship_name, 0, int(app_folder))
        else:
            return (scholarship_name, 1, app_folder)
    
    applications.sort(key=sort_key)
    return applications


def generate_individual_report(
    app_dir: Path,
    report_file: Path,
    template: str,
    generation_date: str,
    verbose: bool = True
) -> bool:
    """
    Generate an individual markdown report for an application if it doesn't exist.
    
    Args:
        app_dir: Path to the application folder
        report_file: Path where the report should be saved
        template: Template string for the report
        generation_date: Date string for report generation
        verbose: Whether to print progress
        
    Returns:
        True if report was generated or already exists, False on error
    """
    # If report already exists, skip
    if report_file.exists():
        return True
    
    try:
        # Load application profile
        application_profile_file = app_dir / "application_profile.json"
        if not application_profile_file.exists():
            if verbose:
                print(f"    WARNING: application_profile.json not found in {app_dir.name}, skipping")
            return False
        
        with open(application_profile_file, 'r', encoding='utf-8') as f:
            application_profile = json.load(f)
        
        # Generate report
        report = generate_report(application_profile, template, generation_date)
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        if verbose:
            total_score = application_profile.get('total_score_summary', {}).get('total_score', 0)
            print(f"    Generated: {report_file.name} (Total score: {total_score})")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"    ERROR: Failed to generate report for {app_dir.name}: {str(e)}")
        log_exception(e, "step4.py", f"generate_individual_report: {app_dir.name}")
        return False


def combine_markdown_reports(report_files: List[Path], verbose: bool = True) -> str:
    """
    Combine multiple markdown report files into a single document.
    
    Args:
        report_files: List of paths to markdown report files
        verbose: Whether to print progress
        
    Returns:
        Combined markdown content as a string
    """
    combined = []
    
    # Add title page
    combined.append("# WAI Scholarship Application Review Reports\n")
    combined.append(f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*\n")
    combined.append(f"*Total Applications: {len(report_files)}*\n")
    combined.append("\n---\n\n")
    
    for i, report_file in enumerate(report_files, 1):
        if verbose:
            scholarship_name = report_file.parts[-3] if len(report_file.parts) >= 3 else "Unknown"
            app_folder = report_file.parts[-2] if len(report_file.parts) >= 2 else "Unknown"
            print(f"  [{i}/{len(report_files)}] Adding: {scholarship_name}/{app_folder}")
        
        # Add page break marker before each report (except the first)
        if i > 1:
            combined.append("\n\n<!-- PAGE_BREAK -->\n\n")
        
        # Add report content
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                combined.append(content)
                combined.append("\n\n")
        except Exception as e:
            error_msg = f"# Error Loading Report\n\nCould not load report from {report_file}: {str(e)}\n\n"
            combined.append(error_msg)
            if verbose:
                print(f"    WARNING: Could not read {report_file}: {e}")
    
    return "\n".join(combined)


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
    try:
        if verbose:
            print(f"  Generating PDF: {output_pdf_path.name}")
        
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
        print(f"  ERROR: Failed to generate PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Step 4: Combine review reports and generate PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Combine all reports and generate PDF
  python code/step4.py

  # Combine reports for a specific scholarship
  python code/step4.py --scholarship-folder "Delaney_Wings"

  # Specify custom output filename
  python code/step4.py --output "combined_reports.pdf"

  # Generate report for top 10 applicants only
  python code/step4.py --scholarship-folder "Delaney_Wings" --limit 10

  # Save combined markdown without generating PDF
  python code/step4.py --markdown-only
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base output directory containing Step 3 reports (default: from OUTPUT_DATA_DIR env var or 'output')"
    )
    
    parser.add_argument(
        "--scholarship-folder",
        type=str,
        default=None,
        help="Combine reports from a specific scholarship folder only (e.g., 'Delaney_Wings')"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output PDF filename (default: 'combined_review_reports.pdf' in {scholarship_folder}/output/)"
    )
    
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Path to custom report template file (default: uses built-in template from step3)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit to top N applicants by total score (default: 0 = process all, use --limit N for top N applicants)"
    )
    
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="Only generate combined markdown file, do not create PDF"
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
        print("Step 4: Combine Reports and Generate PDF")
        print("=" * 60)
        print(f"Output directory: {output_dir}")
        if args.scholarship_folder:
            print(f"Scholarship folder: {args.scholarship_folder}")
        if args.limit and args.limit > 0:
            print(f"Limit: top {args.limit} applicants by total score")
        else:
            print(f"Limit: all applicants")
        print("=" * 60)
    
    # Load template for generating individual reports
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
        print(f"ERROR: No application folders with application_profile.json found in {output_dir}")
        if args.scholarship_folder:
            print(f"  (Looking in scholarship folder: {args.scholarship_folder})")
        sys.exit(1)
    
    if verbose:
        print(f"Found {len(applications)} application folder(s)")
    
    # If limit is specified, read from CSV file to get top applicants
    if args.limit and args.limit > 0:
        if verbose:
            print(f"\nReading CSV file to select top {args.limit} applicants...")
        
        # Determine which scholarship(s) to process
        scholarship_folders_to_process = set()
        if args.scholarship_folder:
            scholarship_folders_to_process.add(args.scholarship_folder)
        else:
            # Extract unique scholarship names from applications
            for scholarship_name, _, _ in applications:
                scholarship_folders_to_process.add(scholarship_name)
        
        # Read CSV files for each scholarship and get top N applicants
        top_applicants: Set[Tuple[str, str]] = set()  # Set of (scholarship_folder, application_folder) tuples
        
        for scholarship_name in scholarship_folders_to_process:
            csv_file = output_dir / scholarship_name / "output" / "applicant_scores_summary.csv"
            
            if not csv_file.exists():
                if verbose:
                    print(f"  WARNING: CSV file not found for {scholarship_name}: {csv_file}")
                    print(f"  CSV file is required when using --limit. Please run step3.py first to generate the CSV.")
                # If CSV doesn't exist, fall back to processing all applications
                continue
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    # CSV is already sorted by total_score (highest first) from step3
                    # Get top N rows for this scholarship
                    top_rows = rows[:args.limit]
                    
                    # Add to top_applicants set
                    for row in top_rows:
                        app_folder = row.get('application_folder', '').strip()
                        if app_folder:
                            top_applicants.add((scholarship_name, app_folder))
                    
                    if verbose:
                        print(f"  Read CSV for {scholarship_name}: {len(top_rows)} top applicant(s)")
                        # Show top scores
                        for i, row in enumerate(top_rows[:min(5, len(top_rows))], 1):
                            app_folder = row.get('application_folder', '')
                            total_score = row.get('total_score', '0')
                            first_name = row.get('first_name', '')
                            last_name = row.get('last_name', '')
                            name = f"{first_name} {last_name}".strip() or app_folder
                            print(f"    #{i}: {app_folder} ({name}) - Total Score: {total_score}")
                        if len(top_rows) > 5:
                            print(f"    ... and {len(top_rows) - 5} more")
                        
            except Exception as e:
                if verbose:
                    print(f"  ERROR: Could not read CSV file for {scholarship_name}: {e}")
                    print(f"  Falling back to processing all applications for this scholarship.")
                # If CSV can't be read, fall back to processing all applications
                continue
        
        # Filter applications to only include top applicants from CSV and sort by CSV order
        if top_applicants:
            original_count = len(applications)
            
            # Create a mapping from (scholarship, application_folder) to the application tuple
            applications_dict = {
                (sch_name, app_dir.name): (sch_name, app_dir, report_file)
                for sch_name, app_dir, report_file in applications
                if (sch_name, app_dir.name) in top_applicants
            }
            
            # Build ordered list from CSV (maintaining CSV order)
            applications_ordered = []
            selected_applicants_log = []
            
            for scholarship_name in scholarship_folders_to_process:
                csv_file = output_dir / scholarship_name / "output" / "applicant_scores_summary.csv"
                if csv_file.exists():
                    try:
                        with open(csv_file, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            rows = list(reader)
                            top_rows = rows[:args.limit]
                            
                            for row in top_rows:
                                app_folder = row.get('application_folder', '').strip()
                                key = (scholarship_name, app_folder)
                                
                                if key in applications_dict:
                                    # Add to ordered applications list in CSV order
                                    applications_ordered.append(applications_dict[key])
                                    
                                    # Also add to log
                                    first_name = row.get('first_name', '').strip()
                                    last_name = row.get('last_name', '').strip()
                                    name = f"{first_name} {last_name}".strip() or "Unknown"
                                    wai_number = row.get('wai_application_number', '').strip() or row.get('wai_membership_number', '').strip() or "N/A"
                                    total_score = row.get('total_score', '0').strip()
                                    selected_applicants_log.append({
                                        'scholarship': scholarship_name,
                                        'application_folder': app_folder,
                                        'name': name,
                                        'wai_number': wai_number,
                                        'total_score': total_score
                                    })
                    except Exception:
                        pass  # Skip if CSV can't be read
            
            # Use ordered applications list (sorted by CSV order)
            applications = applications_ordered
            
            if verbose:
                print(f"\nSelected top {len(applications)} applicant(s) from CSV (from {original_count} total)")
            
            # Log selected applicants
            if selected_applicants_log:
                import logging
                extra = {'script_name': 'step4.py'}
                logging.info("Selected applicants from CSV:", extra=extra)
                for i, app in enumerate(selected_applicants_log, 1):
                    logging.info(
                        f"  #{i}: {app['name']} (WAI: {app['wai_number']}, Score: {app['total_score']}, "
                        f"Folder: {app['scholarship']}/{app['application_folder']})",
                        extra=extra
                    )
        else:
            if verbose:
                print("  WARNING: No top applicants found in CSV. Processing all applications.")
    else:
        if verbose:
            print(f"Processing all {len(applications)} application(s)\n")
    
    # Generate individual markdown reports if they don't exist
    if verbose:
        print("Generating individual markdown reports...")
    
    report_files = []
    generated_count = 0
    existing_count = 0
    
    for i, (scholarship_name, app_dir, report_file) in enumerate(applications, 1):
        if verbose and len(applications) > 1:
            print(f"  [{i}/{len(applications)}] {scholarship_name}/{app_dir.name}")
        
        if report_file.exists():
            existing_count += 1
            if verbose:
                print(f"    Already exists: {report_file.name}")
        else:
            if generate_individual_report(app_dir, report_file, template, generation_date, verbose):
                generated_count += 1
            else:
                continue  # Skip if generation failed
        
        report_files.append(report_file)
    
    if verbose:
        print(f"\n  Generated: {generated_count} new report(s)")
        print(f"  Already existed: {existing_count} report(s)")
        print(f"  Total: {len(report_files)} report(s)\n")
    
    if not report_files:
        print("ERROR: No reports available to combine")
        sys.exit(1)
    
    # Combine markdown reports
    if verbose:
        print("Combining markdown reports...")
    
    combined_markdown = combine_markdown_reports(report_files, verbose)
    
    # Save to output subfolder within scholarship folder
    # If processing a specific scholarship, use that folder, otherwise use first scholarship from applications
    if args.scholarship_folder:
        scholarship_name = args.scholarship_folder
    elif applications:
        # Get scholarship name from first application
        scholarship_name = applications[0][0]
    else:
        scholarship_name = "combined"
    
    scholarship_output_dir = output_dir / scholarship_name / "output"
    scholarship_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save combined markdown
    markdown_output_file = scholarship_output_dir / "combined_review_reports.md"
    with open(markdown_output_file, 'w', encoding='utf-8') as f:
        f.write(combined_markdown)
    
    if verbose:
        print(f"\nSaved combined markdown: {markdown_output_file}")
    
    # Generate PDF if not markdown-only
    if not args.markdown_only:
        if verbose:
            print("\nConverting to PDF...")
        
        # Determine PDF output path
        if args.output:
            pdf_output_file = Path(args.output)
            # If output is a relative path, put it in the scholarship output directory
            if not pdf_output_file.is_absolute():
                pdf_output_file = scholarship_output_dir / pdf_output_file.name
        else:
            pdf_output_file = scholarship_output_dir / "combined_review_reports.pdf"
        
        # Convert markdown to PDF
        success = markdown_to_pdf(combined_markdown, pdf_output_file, verbose)
        
        if not success:
            print("ERROR: PDF generation failed")
            sys.exit(1)
        
        if verbose:
            print(f"\nPDF saved: {pdf_output_file}")
    
    if verbose:
        print("\n" + "=" * 60)
        print("Step 4 Complete")
        print("=" * 60)
        print(f"Combined markdown: {markdown_output_file}")
        if not args.markdown_only:
            print(f"PDF file: {pdf_output_file}")
        print("=" * 60)
    
    # Log summary
    summary = {
        "total_applications_found": len(find_application_folders(output_dir, args.scholarship_folder)),
        "total_reports": len(report_files),
        "generated_reports": generated_count,
        "existing_reports": existing_count,
        "limit_applied": args.limit if (args.limit and args.limit > 0) else "all",
        "combined_markdown": str(markdown_output_file),
        "pdf_generated": not args.markdown_only
    }
    if not args.markdown_only:
        summary["pdf_file"] = str(pdf_output_file)
    
    log_summary("step4.py", summary)
    
    sys.exit(0)


if __name__ == "__main__":
    try:
        # Parse arguments first to get script name and args for logging
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--scholarship-folder", type=str, default=None)
        parser.add_argument("--output-dir", type=str, default=None)
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--template", type=str, default=None)
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--markdown-only", action="store_true")
        parser.add_argument("--quiet", action="store_true")
        
        # Parse known args only (don't error on unknown)
        args, _ = parser.parse_known_args()
        
        # Prepare args dict for logging
        log_args = {
            "scholarship_folder": args.scholarship_folder,
            "output_dir": args.output_dir,
            "output": args.output,
            "template": args.template,
            "limit": args.limit if args.limit and args.limit > 0 else "all",
            "markdown_only": args.markdown_only,
            "quiet": args.quiet
        }
        
        # Use execution logger
        with execution_logger("step4.py", log_args):
            main()
    except Exception as e:
        log_exception(e, "step4.py", "main execution")
        raise
