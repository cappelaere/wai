#!/usr/bin/env python3
"""
Base Agent class for all specialized scholarship analysis agents.

Provides common functionality for Ollama integration, error handling, and
response parsing across all agent types.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import ollama
from jsonschema import validate, ValidationError

from processor.agents.json_parser import JSONParser


logger = logging.getLogger(__name__)


class OllamaConnectionError(Exception):
    """Raised when Ollama server cannot be reached."""
    pass


class OllamaModelError(Exception):
    """Raised when the specified model is not available."""
    pass


class BaseAgent:
    """
    Base class for all scholarship analysis agents.

    Provides:
    - Ollama connection management and validation
    - LLM response parsing (JSON extraction from markdown code blocks)
    - Retry logic with exponential backoff
    - Consistent error handling across all agents
    """

    # Default retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 2  # seconds

    def __init__(
        self,
        model_name: str = "llama3.2",
        ollama_host: Optional[str] = None,
        validate_connection: bool = True,
        schema_name: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        """
        Initialize the Base Agent with Ollama.

        Args:
            model_name: Name of the Ollama model to use (e.g., "llama3.2", "mistral", "phi3")
                       Default: "llama3.2"
            ollama_host: Optional custom Ollama host URL. Falls back to OLLAMA_HOST environment
                        variable, then defaults to http://localhost:11434
            validate_connection: If True, test connection to Ollama on initialization.
                               If False, defer connection test until first use.
            schema_name: Optional name of schema file to load (e.g., "personal_agent_schema.json")
            system_message: Optional system message for structured output. If None, uses default.

        Raises:
            OllamaConnectionError: If validate_connection=True and Ollama is unreachable
            OllamaModelError: If validate_connection=True and model is not available
        """
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._connection_tested = False
        self.schema = None
        self.system_message = system_message or (
            "You are a structured data extraction agent. You MUST respond with valid JSON only. "
            "Do NOT include markdown code blocks, comments, or any text outside the JSON. "
            "Use double quotes only, no trailing commas, and ensure all JSON is parseable by json.loads()."
        )

        # Load schema if provided
        if schema_name:
            self.schema = self._load_schema(schema_name)

        if validate_connection:
            self._validate_ollama_connection()
            self._connection_tested = True

    def _validate_ollama_connection(self) -> None:
        """
        Test connection to Ollama server and verify model availability.

        Raises:
            OllamaConnectionError: If Ollama server cannot be reached
            OllamaModelError: If the specified model is not available locally
        """
        try:
            # Check if Ollama is running and model is available
            models_response = ollama.list()
            # ollama.list() returns a ListResponse object with a 'models' attribute
            # Each model is a Model object with a 'model' attribute containing the name
            model_list = models_response.models if hasattr(models_response, 'models') else []
            model_names = [m.model for m in model_list if hasattr(m, 'model')]

            if self.model_name not in model_names:
                logger.warning(
                    f"Model '{self.model_name}' not found locally. "
                    f"Available models: {', '.join(model_names) if model_names else 'None'}"
                )
                logger.info(f"To download the model, run: ollama pull {self.model_name}")
                logger.info(f"Attempting to use '{self.model_name}' anyway (it will be downloaded if needed)...")
        except Exception as e:
            error_msg = (
                f"Cannot connect to Ollama at {self.ollama_host}. "
                f"Error: {str(e)}. "
                f"Make sure Ollama is running with: ollama serve"
            )
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg)

    def _chat_with_retry(
        self,
        messages: List[Dict[str, str]],
        max_retries: Optional[int] = None,
        timeout: float = 60.0,
        system_message: Optional[str] = None
    ) -> str:
        """
        Send a chat request to Ollama with automatic retry on failure.

        Uses exponential backoff strategy: 2s, 4s, 8s between retries.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_retries: Maximum number of retry attempts. Default: MAX_RETRIES class variable
            timeout: Timeout in seconds for each attempt (note: current ollama library doesn't support this)
            system_message: Optional system message to prepend to messages for structured output

        Returns:
            The response text from the model

        Raises:
            OllamaConnectionError: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = self.MAX_RETRIES

        # Prepend system message if provided
        final_messages = messages
        if system_message:
            # Check if first message is already a system message
            if messages and messages[0].get('role') == 'system':
                final_messages = messages  # Use existing system message
            else:
                final_messages = [{"role": "system", "content": system_message}] + messages

        last_error = None

        for attempt in range(max_retries):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=final_messages,
                    stream=False,
                    options={"temperature": 0}  # Lower temperature for more deterministic JSON output
                )
                return response['message']['content']
            except (ConnectionError, TimeoutError, ollama.ResponseError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = self.INITIAL_RETRY_DELAY ** (attempt + 1)
                    logger.warning(
                        f"Ollama request failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time}s... Error: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Ollama request failed after {max_retries} attempts. "
                        f"Last error: {str(e)}"
                    )

        raise OllamaConnectionError(
            f"Failed to get response from Ollama after {max_retries} attempts. "
            f"Last error: {str(last_error)}"
        )

    def parse_llm_response(self, response_text: str, filename: Optional[str] = None, messages: Optional[List[Dict[str, str]]] = None, retry_count: int = 0) -> Dict[str, Any]:
        """
        Parse JSON response from LLM, handling markdown code blocks and formatting issues.

        The LLM may wrap JSON in markdown code blocks like:
        ```json
        {...}
        ```

        This method extracts and parses the JSON, stripping markdown formatting
        and attempting to fix common formatting issues. If all local fixes fail and
        the original messages are provided, it will ask the LLM to fix the JSON.

        Args:
            response_text: Raw response text from the LLM
            filename: Optional filename being processed (for debugging output)
            messages: Optional original messages for LLM retry (for internal use)
            retry_count: Current retry count (for internal use)

        Returns:
            Parsed JSON as a dictionary

        Raises:
            ValueError: If response cannot be parsed as valid JSON
            json.JSONDecodeError: If JSON is malformed
        """
        # Validate and ensure filename is fully qualified
        if filename:
            # Check if filename looks like a path (contains / or \)
            if '/' not in filename and '\\' not in filename and not filename.startswith('~'):
                # If no path separator, it might be just a name
                logger.debug(f"Filename appears to be relative or just a name: {filename}")
            # Check if it's an absolute path
            elif not filename.startswith('/') and not filename.startswith('~') and not (len(filename) > 1 and filename[1] == ':'):
                # Relative path - log a warning
                logger.warning(f"Filename is relative, not absolute: {filename}")

        # Use JSONParser to handle all JSON parsing and recovery
        return JSONParser.parse_json(
            response_text,
            filename=filename,
            schema=self.schema,
            messages=messages,
            chat_function=self._chat_with_retry,
            retry_count=retry_count
        )

    def _load_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Load JSON schema from the schemas directory.

        Args:
            schema_name: Name of the schema file (e.g., "personal_agent_schema.json")

        Returns:
            Loaded schema as a dictionary, or None if not found
        """
        try:
            # Try to find schema in multiple locations
            schema_paths = [
                Path(__file__).parent.parent.parent / "schemas" / schema_name,  # Top-level /schemas
                Path(__file__).parent / "schemas" / schema_name,  # Agent-level /schemas
            ]

            for schema_path in schema_paths:
                if schema_path.exists():
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                    logger.info(f"Loaded schema from {schema_path}")
                    return schema

            logger.warning(f"Schema file not found: {schema_name}")
            return None

        except Exception as e:
            logger.error(f"Error loading schema {schema_name}: {str(e)}")
            return None

    def _validate_against_schema(self, data: Dict[str, Any], filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Validate data against the loaded schema.

        Args:
            data: Data to validate
            filename: Optional filename for debugging

        Returns:
            The validated data if valid, None if invalid

        Raises:
            ValidationError: If data doesn't match schema
        """
        if not self.schema:
            logger.debug("No schema loaded, skipping validation")
            return data

        try:
            validate(instance=data, schema=self.schema)
            logger.info(f"Data validation successful{' (file: ' + filename + ')' if filename else ''}")
            return data
        except ValidationError as e:
            file_context = f" (file: {filename})" if filename else ""
            logger.error(f"Schema validation failed{file_context}: {str(e)}")
            raise

    def _ensure_connection(self) -> None:
        """
        Ensure Ollama connection has been validated.

        Called before first LLM request if validate_connection was False
        during initialization.
        """
        if not self._connection_tested:
            self._validate_ollama_connection()
            self._connection_tested = True
