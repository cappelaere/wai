#!/usr/bin/env python3
"""
JSON parsing utilities for LLM responses.

Provides robust JSON parsing with structured output validation using the
instructor library, with fallback strategies for malformed JSON.
"""

import json
import re
import logging
from typing import Optional, Dict, List, Any, Type, TypeVar
from json_repair import repair_json
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class JSONParser:
    """Robust JSON parser for LLM responses with multiple recovery strategies.

    Uses the instructor library for structured output validation when available,
    with fallback to traditional JSON parsing and repair strategies.
    """

    @staticmethod
    def parse_json(
        response_text: str,
        filename: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        chat_function = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Parse JSON response from LLM with robust error handling and recovery.

        The LLM may wrap JSON in markdown code blocks like:
        ```json
        {...}
        ```

        This method attempts multiple strategies to parse and repair JSON:
        1. Direct JSON parsing
        2. json_repair library (fixes common issues)
        3. Smart quote and trailing comma fixes
        4. Brace extraction (find balanced JSON object)
        5. LLM retry (ask LLM to fix the JSON)

        Args:
            response_text: Raw response text from the LLM
            filename: Optional filename being processed (for debugging)
            schema: Optional JSON schema to validate against
            messages: Optional original messages for LLM retry
            chat_function: Optional callback function for LLM retry (should take messages list and return string)
            retry_count: Current retry count (for internal use)

        Returns:
            Parsed JSON as a dictionary

        Raises:
            ValueError: If response cannot be parsed as valid JSON after all attempts
        """
        file_context = f" (file: {filename})" if filename else ""

        # Remove markdown code block markers if present
        text = JSONParser._remove_markdown_wrapper(response_text)

        if not text:
            raise ValueError("Empty response after removing markdown formatting")

        # Attempt 1: Direct JSON parsing
        try:
            parsed = json.loads(text)
            JSONParser._validate_against_schema(parsed, schema, file_context)
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"First attempt to parse JSON failed{file_context}: {str(e)}. Attempting to fix...")
            logger.warning(f"Failed to parse text{file_context}:\n{text} <-----")

        # Attempt 2: Use json_repair library
        try:
            logger.info(f"Attempting json_repair{file_context}...")
            text_fixed = repair_json(text)
            result = json.loads(text_fixed)
            logger.info(f"Successfully repaired JSON{file_context} using json_repair")
            JSONParser._validate_against_schema(result, schema, file_context)
            return result
        except Exception as repair_error:
            logger.warning(f"json_repair attempt failed{file_context}: {str(repair_error)}")

        # Attempt 3: Manual fixes (smart quotes, trailing commas)
        text_fixed = JSONParser._apply_manual_fixes(text)

        try:
            result = json.loads(text_fixed)
            logger.info(f"Successfully parsed JSON after manual fixes{file_context}")
            JSONParser._validate_against_schema(result, schema, file_context)
            return result
        except json.JSONDecodeError as e2:
            logger.warning(f"Second attempt failed{file_context}: {str(e2)}. Trying to extract JSON object...")
            logger.debug(f"Failed to parse fixed text{file_context}:\n{text_fixed}")

        # Attempt 4: Extract JSON object by finding balanced braces
        extracted_text = JSONParser._extract_json_object(text_fixed)
        if extracted_text:
            try:
                result = json.loads(extracted_text)
                logger.info(f"Successfully parsed extracted JSON object{file_context}")
                JSONParser._validate_against_schema(result, schema, file_context)
                return result
            except json.JSONDecodeError as e3:
                logger.error(f"Failed to parse JSON after extracting object{file_context}: {str(e3)}")
                logger.debug(f"Extracted text was:\n{extracted_text}")

        logger.error(f"Failed to parse JSON response after all fix attempts{file_context}")
        logger.error(f"Original response text{file_context}:\n{response_text}")
        logger.error(f"Fixed text{file_context}:\n{text_fixed}")

        # Attempt 5: Ask LLM to fix the JSON
        if messages and chat_function and retry_count < 2:  # Allow 2 retries
            logger.warning(f"Asking LLM to fix malformed JSON{file_context} (attempt {retry_count + 1}/2)...")
            try:
                # Build retry message with schema requirements if available
                validation_error_msg = ""
                if schema:
                    # Include schema requirements in retry message
                    required_fields = schema.get('required', [])
                    if required_fields:
                        validation_error_msg = f"\n\nRequired fields: {', '.join(required_fields)}\n"
                
                retry_content = f"""You previously returned malformed JSON. Here is what you returned:

{response_text[:2000]}{validation_error_msg}

CRITICAL: Fix and return ONLY valid JSON that:
1. Is semantically identical to the original response
2. Is valid JSON (parseable by json.loads())
3. Does NOT include markdown code blocks (```json or ```)
4. Does NOT include any text before or after the JSON
5. Uses double quotes only (no single quotes)
6. Has no trailing commas
7. Matches the required schema structure"""

                retry_messages = messages + [
                    {
                        "role": "user",
                        "content": retry_content
                    }
                ]

                retry_response = chat_function(retry_messages)

                logger.info(f"LLM provided retry response{file_context}, attempting to parse...")
                return JSONParser.parse_json(
                    retry_response,
                    filename=filename,
                    schema=schema,
                    messages=None,
                    chat_function=chat_function,
                    retry_count=retry_count + 1
                )

            except Exception as retry_error:
                logger.error(f"LLM retry also failed{file_context}: {str(retry_error)}")

        raise ValueError(f"Could not parse JSON{file_context} after all recovery attempts")

    @staticmethod
    def _remove_markdown_wrapper(text: str) -> str:
        """Remove markdown code block wrapper from text.

        Args:
            text: Text that may be wrapped in markdown code blocks

        Returns:
            Text with markdown wrappers removed
        """
        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    @staticmethod
    def _apply_manual_fixes(text: str) -> str:
        """Apply manual fixes for common JSON formatting issues.

        Args:
            text: Raw JSON text

        Returns:
            Fixed JSON text
        """
        # Replace smart quotes with regular quotes
        text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")

        # Remove trailing commas before closing braces/brackets
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        return text

    @staticmethod
    def _extract_json_object(text: str) -> Optional[str]:
        """Extract JSON object by finding balanced braces.

        Args:
            text: Text containing a JSON object

        Returns:
            Extracted JSON string or None if no balanced object found
        """
        start_idx = text.find('{')
        if start_idx == -1:
            return None

        brace_count = 0
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx:i + 1]

        return None

    @staticmethod
    def _validate_against_schema(
        data: Dict[str, Any],
        schema: Optional[Dict[str, Any]],
        file_context: str = ""
    ) -> None:
        """Validate data against JSON schema if provided.

        Args:
            data: Data to validate
            schema: JSON schema to validate against
            file_context: Context for logging (e.g., filename)

        Raises:
            ValidationError: If validation fails
        """
        if not schema:
            return

        try:
            validate(instance=data, schema=schema)
            logger.info(f"Data validation successful{file_context}")
        except ValidationError as e:
            logger.warning(f"Schema validation failed{file_context}: {str(e)}")
            raise

    @staticmethod
    def parse_with_instructor(
        response_text: str,
        output_model: Type[T],
        filename: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        chat_function = None,
        retry_count: int = 0
    ) -> T:
        """
        Parse JSON response using instructor's structured output validation.

        This method uses the instructor library to validate responses against
        a Pydantic model definition, providing type safety and validation.

        Args:
            response_text: Raw response text from the LLM
            output_model: Pydantic model defining expected output structure
            filename: Optional filename being processed (for debugging)
            messages: Optional original messages for LLM retry
            chat_function: Optional callback function for LLM retry
            retry_count: Current retry count (for internal use)

        Returns:
            Parsed and validated output as the specified model type

        Raises:
            ValueError: If response cannot be parsed and validated after all attempts
        """
        try:
            import instructor
        except ImportError:
            logger.warning("instructor library not available, falling back to standard JSON parsing")
            # Fallback: parse as JSON and validate against model
            parsed_json = JSONParser.parse_json(
                response_text,
                filename=filename,
                schema=None,
                messages=messages,
                chat_function=chat_function,
                retry_count=retry_count
            )
            return output_model(**parsed_json)

        file_context = f" (file: {filename})" if filename else ""

        # Remove markdown wrapper first
        text = JSONParser._remove_markdown_wrapper(response_text)

        if not text:
            raise ValueError("Empty response after removing markdown formatting")

        # Attempt 1: Direct parsing with instructor validation
        try:
            logger.info(f"Parsing with instructor{file_context}...")
            # Use instructor's validation on the JSON text
            parsed_json = json.loads(text)
            validated = output_model(**parsed_json)
            logger.info(f"Successfully validated JSON with instructor{file_context}")
            return validated
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Instructor validation failed{file_context}: {str(e)}")

        # Attempt 2: Try with json_repair
        try:
            logger.info(f"Attempting json_repair for instructor validation{file_context}...")
            text_fixed = repair_json(text)
            parsed_json = json.loads(text_fixed)
            validated = output_model(**parsed_json)
            logger.info(f"Successfully validated repaired JSON with instructor{file_context}")
            return validated
        except Exception as e:
            logger.warning(f"Repaired JSON instructor validation failed{file_context}: {str(e)}")

        # Attempt 3: Manual fixes and validation
        try:
            text_fixed = JSONParser._apply_manual_fixes(text)
            parsed_json = json.loads(text_fixed)
            validated = output_model(**parsed_json)
            logger.info(f"Successfully validated manually fixed JSON with instructor{file_context}")
            return validated
        except Exception as e:
            logger.warning(f"Manual fixes instructor validation failed{file_context}: {str(e)}")

        # Attempt 4: Extract and validate
        try:
            extracted_text = JSONParser._extract_json_object(text_fixed)
            if extracted_text:
                parsed_json = json.loads(extracted_text)
                validated = output_model(**parsed_json)
                logger.info(f"Successfully validated extracted JSON with instructor{file_context}")
                return validated
        except Exception as e:
            logger.warning(f"Extracted JSON instructor validation failed{file_context}: {str(e)}")

        logger.error(f"Failed to parse and validate with instructor after all attempts{file_context}")
        logger.error(f"Original response text{file_context}:\n{response_text}")

        # Attempt 5: Ask LLM to fix
        if messages and chat_function and retry_count < 2:  # Allow 2 retries
            logger.warning(f"Asking LLM to fix malformed JSON for instructor validation{file_context} (attempt {retry_count + 1}/2)...")
            try:
                retry_content = f"""You previously returned malformed JSON. Here is what you returned:

{response_text[:2000]}

CRITICAL: Fix and return ONLY valid JSON that:
1. Is semantically identical to the original response
2. Is valid JSON (parseable by json.loads())
3. Does NOT include markdown code blocks (```json or ```)
4. Does NOT include any text before or after the JSON
5. Uses double quotes only (no single quotes)
6. Has no trailing commas
7. Matches the required output model structure"""

                retry_messages = messages + [
                    {
                        "role": "user",
                        "content": retry_content
                    }
                ]

                retry_response = chat_function(retry_messages)

                logger.info(f"LLM provided retry response for instructor validation{file_context}")
                return JSONParser.parse_with_instructor(
                    retry_response,
                    output_model,
                    filename=filename,
                    messages=None,
                    chat_function=chat_function,
                    retry_count=retry_count + 1
                )

            except Exception as retry_error:
                logger.error(f"LLM retry with instructor validation also failed{file_context}: {str(retry_error)}")

        raise ValueError(f"Could not parse and validate JSON with instructor{file_context} after all recovery attempts")
