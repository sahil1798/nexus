import json
import sys
sys.path.insert(0, '.')

from nexus_core.config import ask_gemini
from nexus_core.models import ToolInfo, SemanticProfile


def profile_server(server_name: str, tools: list[ToolInfo]) -> SemanticProfile:
    """
    Takes raw tool metadata from an MCP server and produces
    a rich semantic profile using AI reasoning.
    """
    tools_description = ""
    for tool in tools:
        tools_description += f"""
Tool: {tool.name}
Description: {tool.description}
Input Schema: {json.dumps(tool.input_schema, indent=2)}
Output Schema: {json.dumps(tool.output_schema, indent=2)}
---
"""

    prompt = f"""You are analyzing an MCP server's capabilities. Given the following metadata, produce a rich semantic profile.

SERVER NAME: {server_name}

TOOLS:
{tools_description}

Produce a JSON response in EXACTLY this format, nothing else:
{{
    "plain_language_summary": "What this server does in simple terms",
    "capability_tags": ["tag1", "tag2", "tag3"],
    "input_concepts": ["what real-world things this server needs as input"],
    "output_concepts": ["what real-world things this server produces"],
    "use_cases": ["concrete scenario 1", "concrete scenario 2", "concrete scenario 3"],
    "compatible_with": ["what kinds of other capabilities would chain well with this, both upstream and downstream"],
    "domain": "primary domain like NLP, web, communication, analytics"
}}

Be thorough. Think about non-obvious use cases. Think about what OTHER tools would pair well with this one.
"""

    raw = ask_gemini(prompt)

    # Clean markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    parsed = json.loads(raw)

    return SemanticProfile(**parsed)
