#!/usr/bin/env python3
"""
Main script to process WAI scholarship applications.

This script processes one or more application folders within a scholarship directory,
extracting information and generating profiles using Ollama.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Import processing classes
from process_application import (
    ApplicationFileProcessor,
    DoclingTextExtractor,
    AttachmentClassifier
)

# Import logging utilities
from logging_utils import execution_logger, log_exception, log_summary

# Import multiprocessing support
from processing_pool import ProcessingPool

# Load environment variables from .env file
load_dotenv()


def load_personal_criteria(scholarship_folder: str) -> Optional[str]:
    """
    Load personal criteria from input/personal_criteria.txt in the scholarship folder.
    
    Args:
        scholarship_folder: Path to the scholarship folder
        
    Returns:
        Criteria text as string, or None if file doesn't exist
    """
    scholarship_path = Path(scholarship_folder)
    criteria_file = scholarship_path / "input" / "personal_criteria.txt"
    
    if criteria_file.exists():
        try:
            with open(criteria_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read personal_criteria.txt: {e}")
            return None
    return None


def load_recommendation_criteria(scholarship_folder: str) -> Optional[str]:
    """
    Load recommendation criteria from input/recommendation_criteria.txt in the scholarship folder.
    
    Args:
        scholarship_folder: Path to the scholarship folder
        
    Returns:
        Criteria text as string, or None if file doesn't exist
    """
    scholarship_path = Path(scholarship_folder)
    criteria_file = scholarship_path / "input" / "recommendation_criteria.txt"
    
    if criteria_file.exists():
        try:
            with open(criteria_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read recommendation_criteria.txt: {e}")
            return None
    return None


def load_application_criteria(scholarship_folder: str) -> Optional[str]:
    """
    Load application criteria from input/application_criteria.txt in the scholarship folder.
    
    Args:
        scholarship_folder: Path to the scholarship folder
        
    Returns:
        Criteria text as string, or None if file doesn't exist
    """
    scholarship_path = Path(scholarship_folder)
    criteria_file = scholarship_path / "input" / "application_criteria.txt"
    
    if criteria_file.exists():
        try:
            with open(criteria_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read application_criteria.txt: {e}")
            return None
    return None


def process_single_application(
    folder_path: str,
    model_name: str,
    output_dir: Optional[str] = None,
    scholarship_folder_name: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """
    Process a single application folder.
    
    Args:
        folder_path: Path to the application folder
        model_name: Ollama model name to use
        output_dir: Base output directory for JSON files
        scholarship_folder_name: Name of the scholarship folder to append to output path
        verbose: Whether to print progress messages
        
    Returns:
        Dictionary with processing result including success status and output file path
    """
    folder_path_obj = Path(folder_path)
    application_folder = folder_path_obj.name
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing application folder: {folder_path}")
        print(f"{'='*60}")
    
    try:
        # Step 1: List files and identify application form
        if verbose:
            print("\n1. Listing files in application folder...")
        processor = ApplicationFileProcessor(str(folder_path))
        files = processor.list_files()
        
        if verbose:
            print(f"   Found {len(files)} files:")
            for filename, attachment_idx in sorted(files):
                file_type = "Application Form" if attachment_idx is None else f"Attachment {attachment_idx}"
                print(f"   - {filename} ({file_type})")
        
        # Step 2: Get application form
        if verbose:
            print("\n2. Identifying application form...")
        app_form_path = processor.get_application_form()
        if not app_form_path:
            error_msg = f"ERROR: No application form found in {folder_path}"
            if verbose:
                print(f"   {error_msg}")
            return {
                "success": False,
                "folder": application_folder,
                "error": error_msg
            }
        
        # Check if application form is empty or zero bytes
        if app_form_path.stat().st_size == 0:
            error_msg = f"ERROR: Application form is empty (zero bytes): {app_form_path.name}"
            if verbose:
                print(f"   {error_msg}")
            return {
                "success": False,
                "folder": application_folder,
                "error": error_msg
            }
        
        if verbose:
            print(f"   Application form: {app_form_path.name}")
        
        # Step 3: Extract text using docling
        if verbose:
            print("\n3. Extracting text from application form using docling...")
        try:
            # Note: 'extractor' is created once per function call (reused for all files in this folder)
            # to avoid expensive DocumentConverter re-initialization
            if 'extractor' not in locals():
                extractor = DoclingTextExtractor()
            extracted_text = extractor.extract_text(app_form_path)
            if verbose:
                print(f"   Extracted {len(extracted_text)} characters of text")
                print(f"   Preview (first 200 chars): {extracted_text[:200]}...")
        except Exception as e:
            error_msg = f"ERROR: Failed to extract text: {str(e)}"
            if verbose:
                print(f"   {error_msg}")
            return {
                "success": False,
                "folder": application_folder,
                "error": error_msg
            }

        # Step 4: Process attachments
        if verbose:
            print("\n4. Processing attachments...")
        attachments = processor.get_attachments()
        classified_attachments = []
        # Note: Reusing 'extractor' from Step 3 to avoid DocumentConverter re-initialization
        classifier = AttachmentClassifier(model_name=model_name)
        
        # Prepare output directory for text files
        # Include scholarship folder name in output path if provided
        base_output_dir = Path(output_dir)
        if scholarship_folder_name:
            output_path = base_output_dir / scholarship_folder_name / application_folder
        else:
            output_path = base_output_dir / application_folder
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, attachment_path in enumerate(attachments, 1):
            # Skip empty or zero-byte files
            if attachment_path.stat().st_size == 0:
                if verbose:
                    print(f"   Skipping empty file (zero bytes): {attachment_path.name}")
                continue
            
            if verbose:
                print(f"   Processing attachment {i}/{len(attachments)}: {attachment_path.name}")
            
            # Extract text from attachment
            attachment_text = ""
            text_file_path = None
            try:
                attachment_text = extractor.extract_text(attachment_path)
                if verbose:
                    print(f"      Extracted {len(attachment_text)} characters")
                
                # Save extracted text to .txt file if text was extracted
                if attachment_text.strip():
                    # Create text filename based on original filename
                    text_filename = attachment_path.stem + ".txt"
                    text_file_path = output_path / text_filename
                    with open(text_file_path, 'w', encoding='utf-8') as f:
                        f.write(attachment_text)
                    if verbose:
                        print(f"      Saved text to: {text_file_path.name}")
                
            except Exception as e:
                if verbose:
                    print(f"      Warning: Could not extract text: {str(e)}")
                attachment_text = ""
            
            # Classify attachment
            try:
                classification = classifier.classify_attachment(
                    attachment_path, 
                    attachment_text, 
                    attachment_path.name
                )
                # Add text file path if text was saved
                if text_file_path:
                    classification['extracted_text_file'] = text_file_path.name
                classified_attachments.append(classification)
                if verbose:
                    print(f"      Classified as: {classification['category']} (confidence: {classification['confidence']})")
            except Exception as e:
                if verbose:
                    print(f"      Warning: Classification failed: {str(e)}")
                error_classification = {
                    "filename": attachment_path.name,
                    "category": "unknown",
                    "confidence": "low",
                    "reasoning": f"Classification error: {str(e)}",
                    "file_extension": attachment_path.suffix.lower(),
                    "has_text": len(attachment_text) > 0,
                    "is_image": attachment_path.suffix.lower() in ['.png', '.jpg', '.jpeg'],
                    "text_length": len(attachment_text)
                }
                if text_file_path:
                    error_classification['extracted_text_file'] = text_file_path.name
                classified_attachments.append(error_classification)
        
        # Step 5: Save extracted data for Step 2
        if verbose:
            print("\n5. Saving extracted data for Step 2...")
        
        # Save application form extracted text
        application_form_text_file = output_path / "application_form_text.txt"
        with open(application_form_text_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Save file list
        file_list = [f[0] for f in files]
        application_form_data = {
            "application_folder": application_folder,
            "application_form_filename": app_form_path.name,
            "extracted_text_file": "application_form_text.txt",
            "file_list": file_list
        }
        application_form_data_file = output_path / "application_form_data.json"
        with open(application_form_data_file, 'w') as f:
            json.dump(application_form_data, f, indent=2)
        
        # Save attachments separately
        attachments_file = output_path / "attachments.json"
        attachments_data = {
            "application_folder": application_folder,
            "total_attachments": len(classified_attachments),
            "attachments": classified_attachments
        }
        with open(attachments_file, 'w') as f:
            json.dump(attachments_data, f, indent=2)
        
        if verbose:
            print(f"   Saved application form text to: {application_form_text_file.name}")
            print(f"   Saved application form data to: {application_form_data_file.name}")
            print(f"   Saved attachments to: {attachments_file.name}")
        
        return {
            "success": True,
            "folder": application_folder,
            "application_form_data_file": str(application_form_data_file),
            "attachments_file": str(attachments_file),
            "application_form_text_file": str(application_form_text_file)
        }
        
    except Exception as e:
        error_msg = f"ERROR: {str(e)}"
        if verbose:
            print(f"   {error_msg}")
        log_exception(e, "step1.py", f"process_single_application: {application_folder}")
        return {
            "success": False,
            "folder": application_folder,
            "error": error_msg
        }


def _worker_process_application(args_tuple) -> dict:
    """
    Worker function for multiprocessing.

    Must be at module level (not nested) to be picklable.
    Accepts a tuple of arguments since multiprocessing map can only pass one argument per worker.

    Args:
        args_tuple: (folder_path, model_name, output_dir, scholarship_folder_name, verbose)

    Returns:
        Result dictionary from process_single_application
    """
    folder_path, model_name, output_dir, scholarship_folder_name, verbose = args_tuple
    return process_single_application(
        folder_path=folder_path,
        model_name=model_name,
        output_dir=output_dir,
        scholarship_folder_name=scholarship_folder_name,
        verbose=False  # Disable verbose in worker to avoid log spam
    )


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Process WAI scholarship application folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all applications (default behavior)
  python code/step1.py --scholarship-folder "data/2026/Delaney_Wings"
  
  # Process first 5 applications only
  python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --limit 5
  
  # Process all applications (explicit, same as default)
  python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --all
  
  # Process a specific application folder
  python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --application-folder "75179"
  
  # Process with custom model and output directory
  python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --limit 3 --model mistral --output-dir results/
        """
    )
    
    parser.add_argument(
        "--scholarship-folder",
        type=str,
        default=None,
        help="Path to the scholarship folder containing application folders (default: from SCHOLARSHIP_FOLDER env var, or {INPUT_DATA_DIR}/Delaney_Wings)"
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
        "--all",
        action="store_true",
        help="Process all application folders (overrides --limit)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model name to use (default: from OLLAMA_MODEL env var or 'llama3.2')"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base output directory for JSON profile files (default: from OUTPUT_DATA_DIR env var or 'output'). Files are saved as: {output-dir}/{application_folder}/application_profile.json"
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
        help="Number of worker processes for parallel processing (default: 0 = sequential). Set to > 0 to enable multiprocessing. Text extraction is CPU-bound so use up to CPU count."
    )

    args = parser.parse_args()
    
    # Get configuration from arguments or environment variables
    # If not provided, construct from INPUT_DATA_DIR
    if args.scholarship_folder:
        scholarship_folder = args.scholarship_folder
    elif os.getenv("SCHOLARSHIP_FOLDER"):
        scholarship_folder = os.getenv("SCHOLARSHIP_FOLDER")
    else:
        # Use INPUT_DATA_DIR to construct default path
        input_data_dir = os.getenv("INPUT_DATA_DIR", "data/2026")
        scholarship_folder = f"{input_data_dir}/Delaney_Wings"
    
    model_name = args.model or os.getenv("OLLAMA_MODEL", "llama3.2")
    # Use OUTPUT_DATA_DIR from environment if output_dir not specified
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.getenv("OUTPUT_DATA_DIR", "output")
    verbose = not args.quiet
    
    scholarship_path = Path(scholarship_folder)
    
    if not scholarship_path.exists():
        print(f"ERROR: Scholarship folder does not exist: {scholarship_folder}")
        sys.exit(1)
    
    if not scholarship_path.is_dir():
        print(f"ERROR: Path is not a directory: {scholarship_folder}")
        sys.exit(1)
    
    # Extract scholarship folder name for output path
    scholarship_folder_name = scholarship_path.name
    
    # Look for Applications subfolder
    applications_path = scholarship_path / "Applications"
    if not applications_path.exists():
        # Fallback: if Applications subfolder doesn't exist, use scholarship folder directly
        applications_path = scholarship_path
        if verbose:
            print(f"Note: 'Applications' subfolder not found, using scholarship folder directly: {scholarship_path}")
    else:
        if verbose:
            print(f"Found Applications folder: {applications_path}")
    
    # Determine which application folders to process
    if args.application_folder:
        # Process a specific folder
        application_folders = [args.application_folder]
    else:
        # Get all subdirectories (application folders) from Applications subfolder
        application_folders = [
            item.name for item in applications_path.iterdir()
            if item.is_dir() and not item.name.startswith('.')
        ]
        # Sort folders: numeric folders first (sorted numerically), then non-numeric (sorted alphabetically)
        def sort_key(folder_name):
            """Sort key: numeric folders sorted as integers, non-numeric sorted alphabetically."""
            if folder_name.isdigit():
                return (0, int(folder_name))  # Numeric folders first, sorted by integer value
            else:
                return (1, folder_name)  # Non-numeric folders after, sorted alphabetically
        
        application_folders.sort(key=sort_key)
        
        # Apply limit (default is 0 = all, unless --limit N is specified)
        if args.all:
            # Process all folders (--all overrides --limit)
            pass
        elif args.limit == 0 or args.limit is None:
            # Process all folders (0 or None means all)
            pass
        else:
            # Apply limit (N means process first N folders)
            application_folders = application_folders[:args.limit]
    
    if not application_folders:
        print(f"ERROR: No application folders found in {applications_path}")
        sys.exit(1)
    
    # Print summary
    if verbose:
        print("=" * 60)
        print("WAI Scholarship Application Processor")
        print("=" * 60)
        print(f"Scholarship folder: {scholarship_folder}")
        print(f"Applications folder: {applications_path}")
        print(f"Model: {model_name}")
        print(f"Application folders to process: {len(application_folders)}")
        if args.all:
            print(f"Processing all folders (--all flag)")
        if args.limit and args.limit > 0:
            print(f"Limit: {args.limit}")
        elif args.all:
            print(f"Limit: all (--all flag specified)")
        else:
            print(f"Limit: all (default)")
        if scholarship_folder_name:
            print(f"Output directory: {output_dir}/{scholarship_folder_name}/{{application_folder}}/application_profile.json")
        else:
            print(f"Output directory: {output_dir}/{{application_folder}}/application_profile.json")
        print("=" * 60)
    
    # Process each application folder
    if verbose and args.workers > 0:
        print(f"\nUsing {args.workers} worker processes for parallel processing")
        print(f"(Text extraction is CPU-bound)")

    # Prepare arguments for each application folder
    worker_args = [
        (
            str(applications_path / app_folder),
            model_name,
            output_dir,
            scholarship_folder_name,
            verbose
        )
        for app_folder in application_folders
    ]

    # Process using pool
    with ProcessingPool(num_workers=args.workers, use_threading=False, verbose=verbose) as pool:
        if verbose and len(application_folders) > 1:
            print(f"Processing {len(application_folders)} applications...")
        results = pool.map_unordered(
            _worker_process_application,
            worker_args,
            show_progress=verbose
        )

    # Count results
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    
    # Print summary
    print("\n" + "=" * 60)
    print("Processing Summary")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed applications:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['folder']}: {result.get('error', 'Unknown error')}")
    
    print("=" * 60)
    
    # Log summary
    summary = {
        "total_processed": len(results),
        "successful": successful,
        "failed": failed
    }
    if failed > 0:
        failed_folders = [r['folder'] for r in results if not r["success"]]
        summary["failed_folders"] = failed_folders
    
    log_summary("step1.py", summary)
    
    # Exit with error code if any failed
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Parse arguments first to get script name and args for logging
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--scholarship-folder", type=str, default=None)
        parser.add_argument("--application-folder", type=str, default=None)
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--model", type=str, default=None)
        parser.add_argument("--output-dir", type=str, default=None)
        parser.add_argument("--quiet", action="store_true")
        
        # Parse known args only (don't error on unknown)
        args, _ = parser.parse_known_args()
        
        # Prepare args dict for logging
        log_args = {
            "scholarship_folder": args.scholarship_folder,
            "application_folder": args.application_folder,
            "limit": args.limit if (args.limit and args.limit > 0) or args.all else "all",
            "model": args.model,
            "output_dir": args.output_dir,
            "quiet": args.quiet
        }
        
        # Use execution logger
        with execution_logger("step1.py", log_args):
            main()
    except Exception as e:
        log_exception(e, "step1.py", "main execution")
        raise

