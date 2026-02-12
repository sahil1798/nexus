import json
import sys
sys.path.insert(0, '.')

from nexus_core.config import ask_gemini
from nexus_core.models import ServerRecord, GraphEdge


class CapabilityGraph:
    """Stores and analyzes connections between MCP server tools."""

    def __init__(self):
        self.edges: list[GraphEdge] = []

    def analyze_compatibility(self, server_a: ServerRecord, server_b: ServerRecord) -> list[GraphEdge]:
        """
        Use AI to analyze whether tools from server_a can feed into tools from server_b.
        Returns edges for all compatible tool pairs.
        """
        new_edges = []

        for tool_a in server_a.tools:
            for tool_b in server_b.tools:
                edge = self._check_tool_pair(
                    server_a.name, tool_a,
                    server_b.name, tool_b
                )
                if edge and edge.compatibility_type != "incompatible":
                    new_edges.append(edge)
                    self.edges.append(edge)

        return new_edges

    def _check_tool_pair(self, server_a_name: str, tool_a, server_b_name: str, tool_b) -> GraphEdge:
        """Check if tool_a's output can feed into tool_b's input."""

        prompt = f"""Analyze whether these two MCP tools can be chained together (output of Tool A feeding into input of Tool B).

TOOL A (SOURCE):
Server: {server_a_name}
Name: {tool_a.name}
Description: {tool_a.description}
Output Schema: {json.dumps(tool_a.output_schema, indent=2) if tool_a.output_schema else "Returns text/data"}

TOOL B (TARGET):
Server: {server_b_name}
Name: {tool_b.name}
Description: {tool_b.description}
Input Schema: {json.dumps(tool_b.input_schema, indent=2)}

Can Tool A's output be used as Tool B's input?

Return JSON in exactly this format:
{{
    "compatibility_type": "direct" or "translatable" or "incompatible",
    "confidence": 0.0 to 1.0,
    "translation_hint": "description of what mapping/transformation is needed, or empty if direct/incompatible"
}}

- "direct": Output matches input with little/no transformation
- "translatable": Output can be transformed to match input
- "incompatible": No meaningful connection possible
"""

        raw = ask_gemini(prompt)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        parsed = json.loads(raw)

        return GraphEdge(
            source_server=server_a_name,
            source_tool=tool_a.name,
            target_server=server_b_name,
            target_tool=tool_b.name,
            compatibility_type=parsed["compatibility_type"],
            confidence=parsed["confidence"],
            translation_hint=parsed.get("translation_hint", ""),
        )

    def build_from_servers(self, servers: list[ServerRecord]):
        """Analyze all pairs of servers and build the complete graph."""
        print("\n🔍 Building capability graph...")

        for i, server_a in enumerate(servers):
            for server_b in servers:
                if server_a.name == server_b.name:
                    continue

                edges = self.analyze_compatibility(server_a, server_b)
                for edge in edges:
                    symbol = "✅" if edge.compatibility_type == "direct" else "🔄"
                    print(f"   {symbol} {edge.source_server}.{edge.source_tool} → {edge.target_server}.{edge.target_tool} ({edge.compatibility_type}, {edge.confidence:.0%})")

        print(f"\n📊 Graph complete: {len(self.edges)} connections found")

    def find_paths(self, start_server: str, end_server: str, max_hops: int = 4) -> list[list[GraphEdge]]:
        """Find all paths from start to end within max_hops."""
        paths = []
        self._dfs(start_server, end_server, [], paths, max_hops)
        return paths

    def _dfs(self, current: str, target: str, path: list, all_paths: list, remaining_hops: int):
        if remaining_hops < 0:
            return
        if current == target and len(path) > 0:
            all_paths.append(path.copy())
            return

        for edge in self.edges:
            if edge.source_server == current:
                if any(e.source_server == edge.target_server for e in path):
                    continue  # Avoid cycles
                path.append(edge)
                self._dfs(edge.target_server, target, path, all_paths, remaining_hops - 1)
                path.pop()

    def get_edges_from(self, server_name: str) -> list[GraphEdge]:
        """Get all outgoing edges from a server."""
        return [e for e in self.edges if e.source_server == server_name]

    def get_edges_to(self, server_name: str) -> list[GraphEdge]:
        """Get all incoming edges to a server."""
        return [e for e in self.edges if e.target_server == server_name]
