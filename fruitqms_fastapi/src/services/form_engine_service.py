"""
Form engine service: validates submissions against template schemas,
calculates scores, and manages form lifecycle.
"""

from typing import Any, Dict, List, Optional
from src.schemas.qms_forms import FormValidationError, FormValidationResult


# Supported field types and their Python value types
FIELD_TYPE_MAP = {
    "text": str,
    "number": (int, float),
    "boolean": bool,
    "select": str,
    "multi_select": list,
    "date": str,  # ISO date string
    "time": str,  # ISO time string
    "photo": str,  # file path or URL
    "signature": str,  # base64 or URL
}


def _get_all_fields(schema: dict) -> List[dict]:
    """Extract all field definitions from a form schema."""
    fields = []
    for section in schema.get("sections", []):
        for field in section.get("fields", []):
            fields.append(field)
    return fields


def _get_field_map(schema: dict) -> Dict[str, dict]:
    """Build a field_id -> field_definition lookup."""
    return {f["id"]: f for f in _get_all_fields(schema)}


def validate_submission(
    template_schema: dict,
    responses: Dict[str, Any],
) -> FormValidationResult:
    """
    Validate form responses against the template schema.

    Checks:
    - Required fields are present
    - Values match expected types
    - Numeric values are within min/max range
    - Select values are from allowed options
    - Text values respect max_length
    - Conditional requirements are met
    """
    errors: List[FormValidationError] = []
    warnings: List[FormValidationError] = []
    field_map = _get_field_map(template_schema)

    # Check each defined field
    for field_id, field_def in field_map.items():
        validation = field_def.get("validation", {})
        field_type = field_def.get("type", "text")
        label = field_def.get("label", field_id)

        # Get the response value
        response = responses.get(field_id)
        value = response.get("value") if isinstance(response, dict) else response

        # Check required
        is_required = validation.get("required", False)
        if is_required and (value is None or value == "" or value == []):
            errors.append(
                FormValidationError(
                    field_id=field_id,
                    message=f"'{label}' is required",
                )
            )
            continue

        # Skip further validation if no value provided and not required
        if value is None or value == "":
            continue

        # Type checking
        expected_type = FIELD_TYPE_MAP.get(field_type)
        if expected_type and not isinstance(value, expected_type):
            errors.append(
                FormValidationError(
                    field_id=field_id,
                    message=f"'{label}' must be of type {field_type}",
                )
            )
            continue

        # Numeric range validation
        if field_type == "number":
            min_val = validation.get("min")
            max_val = validation.get("max")
            if min_val is not None and value < min_val:
                errors.append(
                    FormValidationError(
                        field_id=field_id,
                        message=f"'{label}' must be at least {min_val}",
                    )
                )
            if max_val is not None and value > max_val:
                errors.append(
                    FormValidationError(
                        field_id=field_id,
                        message=f"'{label}' must be at most {max_val}",
                    )
                )

        # Text length validation
        if field_type == "text":
            max_length = validation.get("max_length")
            if max_length and len(value) > max_length:
                errors.append(
                    FormValidationError(
                        field_id=field_id,
                        message=f"'{label}' must be at most {max_length} characters",
                    )
                )

        # Select value validation
        if field_type == "select":
            options = field_def.get("options", [])
            option_values = [o.get("value", o) if isinstance(o, dict) else o for o in options]
            if option_values and value not in option_values:
                errors.append(
                    FormValidationError(
                        field_id=field_id,
                        message=f"'{label}' must be one of: {', '.join(str(o) for o in option_values)}",
                    )
                )

        # Multi-select validation
        if field_type == "multi_select":
            options = field_def.get("options", [])
            option_values = [o.get("value", o) if isinstance(o, dict) else o for o in options]
            if option_values:
                for v in value:
                    if v not in option_values:
                        errors.append(
                            FormValidationError(
                                field_id=field_id,
                                message=f"'{label}': invalid option '{v}'",
                            )
                        )

    # Check conditional requirements
    for field_id, field_def in field_map.items():
        conditional = field_def.get("conditional")
        if not conditional:
            continue

        response = responses.get(field_id)
        value = response.get("value") if isinstance(response, dict) else response

        # Handle if_false conditionals (e.g., "if door_seal_ok is false, require seal_damage_notes")
        if "if_false" in conditional and value is False:
            cond = conditional["if_false"]
            target_field = cond.get("show_field")
            if target_field and cond.get("require"):
                target_response = responses.get(target_field)
                target_value = (
                    target_response.get("value")
                    if isinstance(target_response, dict)
                    else target_response
                )
                if target_value is None or target_value == "":
                    target_label = field_map.get(target_field, {}).get(
                        "label", target_field
                    )
                    errors.append(
                        FormValidationError(
                            field_id=target_field,
                            message=f"'{target_label}' is required when '{field_def.get('label', field_id)}' is No",
                        )
                    )

        # Handle if_true conditionals
        if "if_true" in conditional and value is True:
            cond = conditional["if_true"]
            target_field = cond.get("show_field")
            if target_field and cond.get("require"):
                target_response = responses.get(target_field)
                target_value = (
                    target_response.get("value")
                    if isinstance(target_response, dict)
                    else target_response
                )
                if target_value is None or target_value == "":
                    target_label = field_map.get(target_field, {}).get(
                        "label", target_field
                    )
                    errors.append(
                        FormValidationError(
                            field_id=target_field,
                            message=f"'{target_label}' is required when '{field_def.get('label', field_id)}' is Yes",
                        )
                    )

    # Calculate score if enabled
    score = None
    scoring = template_schema.get("scoring", {})
    if scoring.get("enabled"):
        score = calculate_score(template_schema, responses)

    return FormValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        score=score,
    )


def calculate_score(template_schema: dict, responses: Dict[str, Any]) -> float:
    """
    Calculate a percentage score for pass/fail type forms.

    Counts boolean fields: True = pass, False = fail.
    Score = (passes / total_scored_fields) * 100
    """
    scored = 0
    passed = 0

    for field in _get_all_fields(template_schema):
        if field.get("type") == "boolean":
            response = responses.get(field["id"])
            value = response.get("value") if isinstance(response, dict) else response
            if value is not None:
                scored += 1
                if value is True:
                    passed += 1

    if scored == 0:
        return 100.0

    return round((passed / scored) * 100, 1)
