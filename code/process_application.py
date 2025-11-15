#!/usr/bin/env python3
"""
Process a WAI scholarship application folder.

This script:
1. Lists files in the application folder
2. Identifies the application form (file without attachment index)
3. Extracts text using docling
4. Sends text to Application Agent (Ollama local model)
5. Returns JSON with profile, summary, and completeness score
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import ollama
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat

# Load environment variables from .env file
load_dotenv()


class ApplicationFileProcessor:
    """Process files in an application folder and identify the application form."""
    
    # Regex pattern: ^(\d+)_(\d+)(?:_(\d+))?\.(pdf|docx|png)$
    FILE_PATTERN = re.compile(r'^(\d+)_(\d+)(?:_(\d+))?\.(pdf|docx|png|jpg|jpeg|PDF|DOCX|PNG|JPG|JPEG)$')
    
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
    
    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from a PDF file using docling.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            result = self.converter.convert(str(file_path))
            # Get the text content from the document
            text = result.document.export_to_markdown()
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {file_path}: {str(e)}")


class AttachmentClassifier:
    """Classify attachment files into categories using Ollama."""
    
    def __init__(self, model_name: str = "llama3.2", ollama_host: Optional[str] = None):
        """
        Initialize the Attachment Classifier with Ollama.
        
        Args:
            model_name: Name of the Ollama model to use
            ollama_host: Optional custom Ollama host URL (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    def classify_attachment(self, file_path: Path, extracted_text: str, filename: str) -> Dict:
        """
        Classify an attachment file into one of the categories.
        
        Args:
            file_path: Path to the attachment file
            extracted_text: Extracted text from the file (empty string if no text)
            filename: Name of the file
            
        Returns:
            Dictionary with classification result
        """
        # Determine file type from extension
        file_ext = file_path.suffix.lower()
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        has_text = len(extracted_text.strip()) > 0
        
        prompt = f"""You are classifying a document attachment from a WAI (Women in Aviation International) scholarship application.

File name: {filename}
File extension: {file_ext}
Has extractable text: {has_text}
Is image file: {is_image}

Text content (first 2000 characters):
{extracted_text[:2000] if extracted_text else "No text content available (may be scanned image or empty file)"}

Based on the file name, extension, and any available text content, classify this attachment into ONE of these categories:

1. **recommendation** - A letter of recommendation from a reference
2. **essay** - An essay or personal statement written by the applicant
3. **resume** - A resume or CV listing the applicant's experience and qualifications
4. **medical_certificate** - A medical certificate or FAA medical certificate
5. **flight_log** - A flight logbook or flight hours record
6. **unknown** - Cannot determine the category

Return ONLY a JSON object with this structure:
{{
    "category": "recommendation|essay|resume|medical_certificate|flight_log|unknown",
    "confidence": "high|medium|low",
    "reasoning": "Brief explanation of why this classification was chosen"
}}

Return ONLY valid JSON, no additional text or markdown formatting."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 512
                }
            )
            
            response_text = response['message']['content'].strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx + 1]
            
            result = json.loads(response_text)
            
            # Add file metadata
            result['filename'] = filename
            result['file_extension'] = file_ext
            result['has_text'] = has_text
            result['is_image'] = is_image
            result['text_length'] = len(extracted_text) if extracted_text else 0
            
            return result
            
        except json.JSONDecodeError as e:
            # Fallback classification based on filename and extension
            return {
                "category": "unknown",
                "confidence": "low",
                "reasoning": f"Failed to parse classification response: {str(e)}",
                "filename": filename,
                "file_extension": file_ext,
                "has_text": has_text,
                "is_image": is_image,
                "text_length": len(extracted_text) if extracted_text else 0
            }
        except Exception as e:
            return {
                "category": "unknown",
                "confidence": "low",
                "reasoning": f"Error during classification: {str(e)}",
                "filename": filename,
                "file_extension": file_ext,
                "has_text": has_text,
                "is_image": is_image,
                "text_length": len(extracted_text) if extracted_text else 0
            }


# Main function has been moved to step1.py
# This file now contains only the processing classes
# For backward compatibility, import and run from step1.py
if __name__ == "__main__":
    import subprocess
    import sys
    print("Note: The main function has been moved to step1.py")
    print("Running: python code/step1.py")
    print("-" * 60)
    # Run step1.py with the same arguments
    subprocess.run([sys.executable, "code/step1.py"] + sys.argv[1:])

