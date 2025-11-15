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
from typing import Optional, Dict, List, Any
import ollama


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
        validate_connection: bool = True
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

        Raises:
            OllamaConnectionError: If validate_connection=True and Ollama is unreachable
            OllamaModelError: If validate_connection=True and model is not available
        """
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._connection_tested = False

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
        timeout: float = 60.0
    ) -> str:
        """
        Send a chat request to Ollama with automatic retry on failure.

        Uses exponential backoff strategy: 2s, 4s, 8s between retries.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_retries: Maximum number of retry attempts. Default: MAX_RETRIES class variable
            timeout: Timeout in seconds for each attempt

        Returns:
            The response text from the model

        Raises:
            OllamaConnectionError: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = self.MAX_RETRIES

        last_error = None

        for attempt in range(max_retries):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    stream=False,
                    timeout=timeout
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

    @staticmethod
    def parse_llm_response(response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM, handling markdown code blocks.

        The LLM may wrap JSON in markdown code blocks like:
        ```json
        {...}
        ```

        This method extracts and parses the JSON, stripping markdown formatting.

        Args:
            response_text: Raw response text from the LLM

        Returns:
            Parsed JSON as a dictionary

        Raises:
            ValueError: If response cannot be parsed as valid JSON
            json.JSONDecodeError: If JSON is malformed
        """
        # Remove markdown code block markers if present
        text = response_text.strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        if not text:
            raise ValueError("Empty response after removing markdown formatting")

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response text was: {response_text}")
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
