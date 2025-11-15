#!/usr/bin/env python3
"""
Unified scholarship processing orchestrator.

Orchestrates the complete scholarship application processing pipeline:
- Step 1: Extract applications and classify attachments
- Step 2: Generate application, personal, recommendation, academic, social profiles
- Step 3: Generate review board markdown reports
- Step 4: Combine reports and generate PDF

Provides unified command-line interface with shared arguments for all steps.
Can run individual steps or the complete pipeline.

Usage:
    # Run all steps (default: steps 1-4)
    python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings"

    # Run specific steps
    python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --steps 1 2

    # Run with multiprocessing on step 1 and 2
    python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --workers 4

    # Run with limit and specific steps
    python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --limit 10 --steps 1 2 3
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def clean_output_log(log_file=None):
    """
    Delete output.log file to start fresh logging.

    Args:
        log_file: Path to output.log file (default: output.log in current directory)

    Returns:
        True if deletion successful or file didn't exist, False if error occurred
    """
    if log_file is None:
        log_file = Path("output.log")

    if log_file.exists():
        try:
            log_file.unlink()
            print(f"[OK] Cleaned output log: {log_file}")
            return True
        except Exception as e:
            print(f"[WARN] Could not delete {log_file}: {str(e)}")
            return False
    return True


def run_step(
    step_num: int,
    step_args: List[str],
    verbose: bool = True
) -> Tuple[bool, str]:
    """
    Run a single processing step.

    Args:
        step_num: Step number (1, 2, 3, 4)
        step_args: List of command-line arguments for the step
        verbose: Print output from subprocess

    Returns:
        Tuple of (success: bool, output: str)
    """
    step_file = f"code/step{step_num}.py"

    if not Path(step_file).exists():
        return False, f"Step {step_num} file not found: {step_file}"

    print(f"\n{'='*70}")
    print(f"Step {step_num}: {get_step_description(step_num)}")
    print(f"{'='*70}")
    print(f"Running: python {step_file} {' '.join(step_args)}\n")

    try:
        result = subprocess.run(
            ["python", step_file] + step_args,
            capture_output=not verbose,
            text=True,
            timeout=3600  # 1 hour timeout per step
        )

        if result.returncode == 0:
            print(f"[OK] Step {step_num} completed successfully\n")
            return True, result.stdout
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"[ERROR] Step {step_num} failed with return code {result.returncode}")
            print(f"Error: {error_msg}\n")
            return False, error_msg

    except subprocess.TimeoutExpired:
        return False, f"Step {step_num} timed out after 1 hour"
    except Exception as e:
        return False, f"Error running Step {step_num}: {str(e)}"


def get_step_description(step_num: int) -> str:
    """Get human-readable description of a step."""
    descriptions = {
        1: "Process Applications & Classify Attachments",
        2: "Generate Profiles (Application, Personal, Recommendation, Academic, Social)",
        3: "Generate Review Board Markdown Reports",
        4: "Combine Reports & Generate PDF"
    }
    return descriptions.get(step_num, f"Step {step_num}")


def build_step_args(
    step_num: int,
    scholarship_folder: str,
    output_dir = None,
    limit: int = 0,
    model = None,
    workers: int = 0,
    quiet: bool = False
) -> List[str]:
    """
    Build command-line arguments for a specific step.

    Args:
        step_num: Step number (1, 2, 3, 4)
        scholarship_folder: Path to scholarship folder
        output_dir: Output directory (optional)
        limit: Number of applications to process (0 = all)
        model: Ollama model name (optional)
        workers: Number of worker processes (0 = sequential)
        quiet: Suppress verbose output

    Returns:
        List of command-line arguments
    """
    args = []

    # Step 1 uses --scholarship-folder with full path
    if step_num == 1:
        args.extend(["--scholarship-folder", scholarship_folder])
    # Steps 2-4 use --scholarship-folder with just the folder name
    else:
        folder_name = Path(scholarship_folder).name
        args.extend(["--scholarship-folder", folder_name])

    if output_dir:
        args.extend(["--output-dir", output_dir])

    if limit > 0:
        args.extend(["--limit", str(limit)])

    if model:
        args.extend(["--model", model])

    # Only steps 1 and 2 support workers
    if step_num in [1, 2] and workers > 0:
        args.extend(["--workers", str(workers)])

    if quiet:
        args.append("--quiet")

    return args


def main():
    """Main orchestrator function."""
    parser = argparse.ArgumentParser(
        description="Unified scholarship processing orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all steps (default: 1, 2, 3, 4)
  python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings"

  # Run specific steps only
  python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --steps 1 2

  # Run with multiprocessing (4 workers for steps 1 & 2)
  python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --workers 4

  # Run with limit on first 5 applications
  python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --limit 5

  # Run steps 1 and 2 with 8 workers and limit 10
  python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --steps 1 2 --limit 10 --workers 8

  # Quiet mode (only show errors and final summary)
  python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --quiet
        """
    )

    parser.add_argument(
        "--scholarship-folder",
        type=str,
        required=True,
        help="Path to the scholarship folder (e.g., 'data/2026/Delaney_Wings')"
    )

    parser.add_argument(
        "--steps",
        type=int,
        nargs="+",
        default=[1, 2, 3, 4],
        help="Steps to run (default: 1 2 3 4). Examples: --steps 1 2 or --steps 1 2 3"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of applications to process (default: 0 = all)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model name (default: from OLLAMA_MODEL env var or 'llama3.2')"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base output directory (default: from OUTPUT_DATA_DIR env var or 'output')"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of worker processes for steps 1 & 2 (default: 0 = sequential)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output (only show errors and summary)"
    )

    parser.add_argument(
        "--skip-log-cleanup",
        action="store_true",
        help="Skip deletion of output.log file at start"
    )

    args = parser.parse_args()

    # Normalize steps argument (handle both "1 2 3" and "1,2,3" formats)
    if len(args.steps) == 1 and "," in str(args.steps[0]):
        # Handle case where user passed "1,2,3" as single argument
        steps = [int(s.strip()) for s in str(args.steps[0]).split(",")]
    else:
        steps = sorted(set(args.steps))  # Remove duplicates and sort

    # Validate steps
    valid_steps = {1, 2, 3, 4}
    invalid_steps = set(steps) - valid_steps
    if invalid_steps:
        parser.error(f"Invalid step numbers: {invalid_steps}. Valid steps: {valid_steps}")

    # Clean output log at start (unless skipped)
    if not args.skip_log_cleanup:
        clean_output_log()

    print(f"\n{'='*70}")
    print("Scholarship Application Processing Orchestrator")
    print(f"{'='*70}")
    print(f"Scholarship folder: {args.scholarship_folder}")
    print(f"Steps to run: {steps}")
    if args.limit > 0:
        print(f"Application limit: {args.limit}")
    if args.workers > 0:
        print(f"Worker processes (steps 1 & 2): {args.workers}")
    print(f"{'='*70}\n")

    # Track results
    results = {}
    start_time = time.time()
    failed_step = None

    # Run requested steps
    for step_num in steps:
        step_args = build_step_args(
            step_num=step_num,
            scholarship_folder=args.scholarship_folder,
            output_dir=args.output_dir,
            limit=args.limit,
            model=args.model,
            workers=args.workers,
            quiet=args.quiet
        )

        success, output = run_step(step_num, step_args, verbose=not args.quiet)
        results[step_num] = {
            "success": success,
            "output": output
        }

        if not success:
            failed_step = step_num
            print(f"\n[WARN] Processing stopped at Step {step_num}")
            print(f"Error details:\n{output}")
            break

    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*70}")
    print("Processing Summary")
    print(f"{'='*70}")

    for step_num in steps:
        if step_num in results:
            status = "[OK] COMPLETED" if results[step_num]["success"] else "[ERROR] FAILED"
            print(f"Step {step_num}: {status}")

    print(f"\nTotal time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    print(f"{'='*70}\n")

    if failed_step:
        print(f"[WARN] Processing incomplete due to failure at Step {failed_step}")
        sys.exit(1)
    else:
        print("[OK] All requested steps completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
