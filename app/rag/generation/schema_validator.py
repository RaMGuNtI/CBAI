import json
from typing import Dict, Any, Tuple, Optional
import jsonschema


class JSONSchemaValidator:
    @staticmethod
    def validate_json_response(response_text: str, schema_str: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate whether response_text is valid JSON and conforms to the provided JSON Schema.
        Returns (is_valid, error_message, parsed_json_dict).
        """
        if not response_text:
            return False, "Response is empty", None

        # Clean potential markdown wrapping if present
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON syntax: {str(e)}", None

        if not schema_str or not schema_str.strip():
            return True, None, parsed_data

        try:
            schema_dict = json.loads(schema_str)
            jsonschema.validate(instance=parsed_data, schema=schema_dict)
            return True, None, parsed_data
        except json.JSONDecodeError as e:
            return False, f"Provided schema is not valid JSON: {str(e)}", parsed_data
        except jsonschema.ValidationError as e:
            return False, f"Schema validation error: {e.message}", parsed_data
        except Exception as e:
            return False, f"Schema error: {str(e)}", parsed_data

