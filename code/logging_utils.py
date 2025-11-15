#!/usr/bin/env python3
"""
Logging utilities for tracking execution summaries, elapsed time, and exceptions.
"""

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_log_dir() -> Path:
    """Get the log directory from environment variable or use default."""
    log_dir = os.getenv("LOG_OUTPUT_DIR", "logs")
    return Path(log_dir)


def get_log_file() -> Path:
    """Get the log file path."""
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "output.log"


def log_message(message: str, script_name: str = "unknown"):
    """
    Append a message to the log file with timestamp.
    
    Args:
        message: Message to log
        script_name: Name of the script generating the log
    """
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{script_name}] {message}\n")


def log_exception(exception: Exception, script_name: str = "unknown", context: str = ""):
    """
    Log an exception with full traceback.
    
    Args:
        exception: The exception that occurred
        script_name: Name of the script where exception occurred
        context: Additional context about where the exception occurred
    """
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{script_name}] EXCEPTION: {context}\n")
        f.write(f"Exception Type: {type(exception).__name__}\n")
        f.write(f"Exception Message: {str(exception)}\n")
        f.write("Traceback:\n")
        traceback.print_exc(file=f)
        f.write("\n")


@contextmanager
def execution_logger(script_name: str, args: Optional[Dict[str, Any]] = None):
    """
    Context manager for logging script execution with timing.
    
    Usage:
        with execution_logger("step1.py", {"limit": 5}):
            # Your code here
            pass
    
    Args:
        script_name: Name of the script being executed
        args: Optional dictionary of command-line arguments
    """
    start_time = datetime.now()
    log_file = get_log_file()
    
    # Log start
    timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] [{script_name}] EXECUTION STARTED\n")
        if args:
            f.write(f"Arguments: {args}\n")
        f.write(f"{'='*80}\n")
    
    try:
        yield
        # Log successful completion
        end_time = datetime.now()
        elapsed = end_time - start_time
        timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{script_name}] EXECUTION COMPLETED\n")
            f.write(f"Elapsed time: {elapsed.total_seconds():.2f} seconds ({elapsed})\n")
            f.write(f"{'='*80}\n\n")
            
    except Exception as e:
        # Log exception and re-raise
        end_time = datetime.now()
        elapsed = end_time - start_time
        timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{script_name}] EXECUTION FAILED\n")
            f.write(f"Elapsed time before failure: {elapsed.total_seconds():.2f} seconds ({elapsed})\n")
            f.write(f"Exception Type: {type(e).__name__}\n")
            f.write(f"Exception Message: {str(e)}\n")
            f.write("Traceback:\n")
            traceback.print_exc(file=f)
            f.write(f"{'='*80}\n\n")
        
        raise


def log_summary(script_name: str, summary: Dict[str, Any]):
    """
    Log an execution summary.
    
    Args:
        script_name: Name of the script
        summary: Dictionary with summary information (e.g., {"total": 10, "successful": 8, "failed": 2})
    """
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{script_name}] SUMMARY:\n")
        for key, value in summary.items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

