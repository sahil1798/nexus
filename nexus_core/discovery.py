import json
import sys
sys.path.insert(0, '.')

from nexus_core.config import ask_gemini
from nexus_core.models import ServerRecord, GraphEdge


class PipelineStep:
    """A single step in a discovered pipeline."""
    def __init__(self, server_name: str, tool_name: str, edge: GraphEdge = None):
        self.server_name = server_name
        self.tool_name = tool_name
        self.edge = edge  # The edge leading INTO this step (None for first step)

    def __repr__(self):
        return f"{self.server_name}.{self.tool_name}"


class Pipeline:
    """A complete discovered pipeline."""
    def __init__(self, steps: list[PipelineStep], confidence: float):
        self.steps = steps
        self.confidence = confidence

    def display(self):
        print(f"\n🛤️  Pipeline (confidence: {self.confidence:.0%}):")
        for i, step in enumerate(self.steps, 1):
            if step.edge:
                edge_type = step.edge.compatibility_type
                symbol = "✅" if edge_type == "direct" else "🔄"
                print(f"   {symbol} Step {i}: {step.server_name}.{step.tool_name} ({edge_type})")
                if step.edge.translation_hint:
                    print(f"         Hint: {step.edge.translation_hint}")
            else:
                print(f"   🚀 Step {i}: {step.server_name}.{step.tool_name} (entry point)")


class DiscoveryEngine:
    """Discovers pipelines to fulfill user requests."""

    def __init__(self, servers: dict[str, ServerRecord], edges: list[GraphEdge]):
        self.servers = servers
        self.edges = edges

    def discover(self, user_request: str) -> Pipeline:
        """
        Given a natural language request, figure out which servers
        to chain together and in what order.
        """
        print(f"\n🔍 Analyzing request: \"{user_request}\"")

        # Build a description of all available capabilities
        capabilities = ""
        for name, record in self.servers.items():
            profile = record.semantic_profile
            tools_desc = ", ".join([t.name for t in record.tools])
            capabilities += f"\nServer: {name}\n"
            capabilities += f"  Tools: {tools_desc}\n"
            capabilities += f"  Summary: {profile.plain_language_summary}\n"
            capabilities += f"  Tags: {', '.join(profile.capability_tags)}\n"

        # Build a description of all known connections
        connections = ""
        for edge in self.edges:
            connections += f"\n  {edge.source_server}.{edge.source_tool} → {edge.target_server}.{edge.target_tool}"
            connections += f" [{edge.compatibility_type}, confidence={edge.confidence}]"
            if edge.translation_hint:
                connections += f" (hint: {edge.translation_hint})"

        prompt = f"""You are a pipeline planner. Given a user request and available MCP servers with their connections, determine the optimal pipeline.

USER REQUEST: "{user_request}"

AVAILABLE SERVERS:
{capabilities}

KNOWN CONNECTIONS (output of one tool can feed into input of another):
{connections}

Determine the best pipeline to fulfill this request.

Return JSON in EXACTLY this format, nothing else:
{{
    "steps": [
        {{
            "server": "server-name",
            "tool": "tool-name",
            "reason": "why this step is needed"
        }}
    ],
    "overall_confidence": 0.85,
    "explanation": "brief explanation of the pipeline"
}}

Rules:
- Only use servers and tools that are listed above
- Prefer paths with known connections
- Order the steps logically (data flows from one to the next)
- If the request cannot be fulfilled, return an empty steps list and explain why
"""

        raw = ask_gemini(prompt)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        parsed = json.loads(raw)

        print(f"\n📋 Pipeline explanation: {parsed.get('explanation', 'N/A')}")

        # Build Pipeline object with edge references
        steps = []
        for i, step_data in enumerate(parsed["steps"]):
            server_name = step_data["server"]
            tool_name = step_data["tool"]

            # Find the edge connecting previous step to this step
            edge = None
            if i > 0:
                prev = parsed["steps"][i - 1]
                edge = self._find_edge(prev["server"], prev["tool"], server_name, tool_name)

            steps.append(PipelineStep(server_name, tool_name, edge))
            print(f"   Step {i+1}: {server_name}.{tool_name} — {step_data['reason']}")

        pipeline = Pipeline(steps, parsed.get("overall_confidence", 0.0))
        return pipeline

    def _find_edge(self, src_server: str, src_tool: str, tgt_server: str, tgt_tool: str) -> GraphEdge:
        """Find an edge between two specific tools."""
        for edge in self.edges:
            if (edge.source_server == src_server and
                edge.source_tool == src_tool and
                edge.target_server == tgt_server and
                edge.target_tool == tgt_tool):
                return edge
        return None
