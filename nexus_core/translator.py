import json
import sys
sys.path.insert(0, '.')

from nexus_core.config import ask_gemini
from nexus_core.models import GraphEdge


class TranslationEngine:
    """Generates and applies data translations between pipeline steps."""

    def __init__(self):
        self.specs_cache: dict[str, dict] = {}

    def generate_spec(self, edge: GraphEdge, source_output: dict, target_input_schema: dict) -> dict:
        """
        Generate a translation specification for transforming
        source tool output into target tool input.
        """
        cache_key = f"{edge.source_server}.{edge.source_tool}->{edge.target_server}.{edge.target_tool}"

        if cache_key in self.specs_cache:
            return self.specs_cache[cache_key]

        # Find required fields from target schema
        required_fields = target_input_schema.get("required", [])

        # Truncate source output values for the prompt — Gemini only needs
        # to see field names and a preview, not the full content
        truncated_output = {}
        for k, v in source_output.items():
            if isinstance(v, str) and len(v) > 200:
                truncated_output[k] = v[:200] + "... [truncated]"
            else:
                truncated_output[k] = v

        prompt = f"""You are a data transformation expert. Generate a mapping specification to transform data from one tool's output to another tool's input.

SOURCE: {edge.source_server}.{edge.source_tool}
SOURCE OUTPUT (actual data):
{json.dumps(truncated_output, indent=2)}

TARGET: {edge.target_server}.{edge.target_tool}
TARGET INPUT SCHEMA:
{json.dumps(target_input_schema, indent=2)}

REQUIRED TARGET FIELDS: {json.dumps(required_fields)}

HINT: {edge.translation_hint}

Generate a JSON mapping specification in EXACTLY this format:
{{
    "mappings": [
        {{
            "target_field": "field name in target input",
            "source_field": "field name from source output, or null if from context",
            "transformation": "description of any transformation needed, or 'direct' if just copy",
            "source": "output or context",
            "required": true or false
        }}
    ],
    "context_fields_needed": ["list of fields that must come from user/pipeline context"]
}}

IMPORTANT RULES:
- ONLY map fields that are in the REQUIRED list, unless there is clear data for optional fields
- Do NOT include optional fields that have defaults (like max_sentences, limit, etc.)
- If a field is optional and you have no specific value for it, LEAVE IT OUT entirely
"""

        raw = ask_gemini(prompt)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            spec = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: generate a basic direct mapping
            spec = {
                "mappings": [
                    {
                        "target_field": field,
                        "source_field": None,
                        "transformation": "direct",
                        "source": "output",
                        "required": True
                    }
                    for field in required_fields
                ],
                "context_fields_needed": required_fields
            }

        self.specs_cache[cache_key] = spec
        return spec

    def apply_translation(self, spec: dict, source_output: dict, context: dict) -> dict:
        """
        Apply a translation specification to transform source data
        into target input format.
        """
        result = {}

        for mapping in spec.get("mappings", []):
            target_field = mapping["target_field"]
            source_field = mapping.get("source_field")
            source_type = mapping.get("source", "output")
            required = mapping.get("required", True)

            if source_type == "context" or source_field is None:
                value = context.get(target_field)
                if value is None:
                    value = context.get(source_field)
            else:
                value = source_output.get(source_field)

            # Only include the field if it has a real value
            if value is not None and value != "":
                result[target_field] = value

        return result
