#!/usr/bin/env python3
"""
Core utilities for processing a WAI scholarship application folder.

This module provides reusable processing classes used by Step 1:
- ApplicationFileProcessor: list / identify application form + attachments
- DoclingTextExtractor: robust text extraction with OCR gibberish filtering
- AttachmentClassifier: classify attachments via Ollama with structured output
  validation using Instructor + Pydantic schemas.

The main CLI logic lives in `processor/pipeline/step1.py`.
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Literal

from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat  # noqa: F401 (kept for future use)

import instructor
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


class ApplicationFileProcessor:
    """Process files in an application folder and identify the application form."""
    
    # Use case‑insensitive regex instead of listing every case variant.
    FILE_PATTERN = re.compile(
        r'^(\d+)_(\d+)(?:_(\d+))?\.(pdf|docx|png|jpg|jpeg)$',
        re.IGNORECASE,
    )
    
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        if not self.folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
    
    def list_files(self) -> List[Tuple[str, Optional[int]]]:
        """
        List all files in the folder and parse their naming convention.
        Skips empty or zero-byte files.
        
        Returns:
            List of tuples: (filename, attachment_index)
            attachment_index is None for the application form, 1+ for attachments
        """
        files = []
        for file_path in self.folder_path.iterdir():
            if file_path.is_file():
                # Skip empty or zero-byte files
                if file_path.stat().st_size == 0:
                    continue
                match = self.FILE_PATTERN.match(file_path.name)
                if match:
                    membership_num, app_num, attachment_idx, ext = match.groups()
                    attachment_index = int(attachment_idx) if attachment_idx else None
                    files.append((file_path.name, attachment_index))
        return files
    
    def get_application_form(self) -> Optional[Path]:
        """
        Get the application form file (the one without attachment index).
        According to the design doc, this should be the last file when sorted.
        """
        files = self.list_files()
        # Filter for application form (attachment_index is None)
        app_forms = [(name, idx) for name, idx in files if idx is None]
        
        if not app_forms:
            return None
        
        # Sort by filename and get the last one (as per user's requirement)
        app_forms.sort(key=lambda x: x[0])
        app_form_name = app_forms[-1][0]
        return self.folder_path / app_form_name
    
    def get_attachments(self) -> List[Path]:
        """Get all attachment files (files with attachment index >= 1)."""
        files = self.list_files()
        attachments = [(name, idx) for name, idx in files if idx is not None]
        attachments.sort(key=lambda x: (x[1], x[0]))  # Sort by index, then name
        return [self.folder_path / name for name, _ in attachments]


class DoclingTextExtractor:
    """Extract text from PDFs using docling."""

    def __init__(self):
        self.converter = DocumentConverter()

    def _clean_extracted_text(self, text: str, min_word_length: int = 2) -> str:
        """
        Clean extracted text by removing garbage lines, single characters, and excessive whitespace.

        This is especially useful for handling OCR output from scanned PDFs.

        Args:
            text: Raw extracted text
            min_word_length: Minimum word length to keep (default: 2)

        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Strip whitespace from line
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip lines with only single characters or very short strings
            # unless they are meaningful punctuation or numbers
            if len(stripped) == 1 and stripped not in '0123456789.,:;!?\'"':
                continue

            # Skip lines that are mostly non-alphanumeric characters (likely OCR garbage)
            alphanumeric_count = sum(1 for c in stripped if c.isalnum() or c.isspace())
            if len(stripped) > 3 and alphanumeric_count / len(stripped) < 0.3:
                continue

            # Skip lines with repeated single characters (like "--------" or "||||")
            if len(set(stripped.replace(' ', ''))) == 1 and len(stripped) > 2:
                continue

            # Skip lines that are mostly whitespace
            if len(stripped.split()) == 0:
                continue

            cleaned_lines.append(stripped)

        # Join cleaned lines and remove excessive blank lines
        result = '\n'.join(cleaned_lines)

        # Replace multiple consecutive blank lines with single blank line
        result = re.sub(r'\n\n\n+', '\n\n', result)

        return result.strip()

    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from a PDF file using docling.

        Args:
            file_path: Path to the PDF file

        Returns:
            Cleaned extracted text as a string
        """
        try:
            result = self.converter.convert(str(file_path))
            # Get the text content from the document
            text = result.document.export_to_markdown()

            # Clean the extracted text to remove OCR garbage
            cleaned_text = self._clean_extracted_text(text)

            # Only return if we have meaningful content (at least 50 characters)
            # If cleaning removed too much, return original to avoid losing all content
            if len(cleaned_text) >= 50:
                return cleaned_text
            elif len(text.strip()) >= 50:
                # If cleaning was too aggressive, return original
                return text
            else:
                # Very short content, return as-is
                return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {file_path}: {str(e)}")


class AttachmentClassifier:
    """
    Rule-based classifier for attachment files using the WAI file naming convention.
    
    We no longer call an LLM here because the file naming convention encodes
    the attachment role:
      - attachment index 1 and 2 -> recommendation
      - attachment index 3       -> resume
      - attachment index 4       -> essay
      - anything else            -> unknown
    """

    def __init__(self, model_name: str = "llama3.2:1b", ollama_host: Optional[str] = None):
        # Model-related arguments are kept for backward compatibility but unused,
        # since classification is now purely rule-based.
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def classify_attachment(self, file_path: Path, extracted_text: str, filename: str) -> Dict:
        """
        Classify an attachment file into one of the categories using naming convention.
    
        Args:
            file_path: Path to the attachment file.
            extracted_text: Extracted text from the file (unused but kept for compatibility).
            filename: Name of the file.
    
        Returns:
            Dictionary with classification result (plus file metadata).
        """
        # Determine file type from extension
        file_ext = file_path.suffix.lower()
        is_image = file_ext in [".png", ".jpg", ".jpeg"]
        has_text = len(extracted_text.strip()) > 0
    
        # Infer attachment index from filename using the same FILE_PATTERN as ApplicationFileProcessor
        attachment_index: Optional[int] = None
        match = ApplicationFileProcessor.FILE_PATTERN.match(filename)
        if match:
            _, _, attachment_idx, _ = match.groups()
            if attachment_idx is not None:
                try:
                    attachment_index = int(attachment_idx)
                except ValueError:
                    attachment_index = None
    
        # Map attachment index to category based on naming convention
        if attachment_index in (1, 2):
            category: Literal[
                "recommendation", "essay", "resume", "medical_certificate", "flight_log", "unknown"
            ] = "recommendation"
            confidence: Literal["high", "medium", "low"] = "high"
            reasoning = (
                "Attachment index 1 or 2 in the naming convention corresponds to a recommendation letter."
            )
        elif attachment_index == 3:
            category = "resume"
            confidence = "high"
            reasoning = "Attachment index 3 in the naming convention corresponds to a resume."
        elif attachment_index == 4:
            category = "essay"
            confidence = "high"
            reasoning = "Attachment index 4 in the naming convention corresponds to an essay."
        else:
            category = "unknown"
            confidence = "low"
            reasoning = (
                "Attachment index is missing or outside the 1–4 range; cannot map to a known category."
            )
    
        result: Dict[str, object] = {
            "category": category,
            "confidence": confidence,
            "reasoning": reasoning,
            "filename": filename,
            "file_extension": file_ext,
            "has_text": has_text,
            "is_image": is_image,
            "text_length": len(extracted_text) if extracted_text else 0,
        }
    
        return result
