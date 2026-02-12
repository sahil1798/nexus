"""
NEXUS Capability Graph with Embeddings + Database
==================================================
Uses vector similarity to find candidate connections efficiently,
then validates with LLM only for high-similarity pairs.
"""

import json
import sys
sys.path.insert(0, '.')

from nexus_core.config import ask_gemini
from nexus_core.models import ServerRecord, GraphEdge
from nexus_core import database as db
from nexus_core.embeddings import EmbeddingIndex


class CapabilityGraph:
    """
    Stores servers and the edges (connections) between their tools.
    Uses embeddings for O(N) candidate discovery instead of O(N²) LLM calls.
    """

    def __init__(self, use_cache: bool = True):
        self.edges: list[GraphEdge] = []
        self.embedding_index = EmbeddingIndex()
        self.use_cache = use_cache

        if use_cache:
            self._load_from_database()

    def _load_from_database(self):
        """Load all edges from database."""
        self.edges = db.load_all_edges()
        if self.edges:
            print(f"📦 Loaded {len(self.edges)} edges from database")

    def build_edges(self, servers: dict[str, ServerRecord], incremental: bool = True):
        """
        Build edges using embedding-based candidate selection.

        Strategy:
        1. Generate embeddings for all tool inputs/outputs (O(N) API calls)
        2. Compute cosine similarity between all pairs (instant, no API calls)
        3. Only call LLM to validate HIGH-SIMILARITY candidates
        """
        if not incremental:
            db.clear_all_edges()
            self.edges = []

        print("\n🔍 Building capability graph...")

        # Step 1: Build embedding index
        self.embedding_index.index_all_servers(servers)

        # Step 2: Find candidates via cosine similarity
        print("\n🔎 Finding candidate connections via embedding similarity...")
        candidates = self.embedding_index.find_candidates(threshold=0.45)
        print(f"   Found {len(candidates)} candidate pairs above threshold")

        # Step 3: Validate candidates with LLM
        new_edges = 0
        cached_edges = 0
        skipped = 0

        for source_key, target_key, similarity in candidates:
            src_server_name, src_tool_name = source_key.split(".", 1)
            tgt_server_name, tgt_tool_name = target_key.split(".", 1)

            # Check if already in database
            if incremental and db.edge_exists(src_server_name, src_tool_name, tgt_server_name, tgt_tool_name):
                cached_edges += 1
                continue

            # Get tool objects
            src_server = servers.get(src_server_name)
            tgt_server = servers.get(tgt_server_name)
            if not src_server or not tgt_server:
                continue

            src_tool = next((t for t in src_server.tools if t.name == src_tool_name), None)
            tgt_tool = next((t for t in tgt_server.tools if t.name == tgt_tool_name), None)
            if not src_tool or not tgt_tool:
                continue

            print(f"   🔬 Validating: {source_key} → {target_key} (similarity: {similarity:.2f})")

            edge = self._evaluate_edge(
                src_server_name, src_tool, src_server.semantic_profile,
                tgt_server_name, tgt_tool, tgt_server.semantic_profile,
            )

            if edge.compatibility_type != "incompatible":
                db.save_edge(edge)
                new_edges += 1
                symbol = "✅" if edge.compatibility_type == "direct" else "🔄"
                print(f"     {symbol} {edge.compatibility_type} (confidence: {edge.confidence})")
            else:
                skipped += 1

        # Reload from database for consistency
        self.edges = db.load_all_edges()

        print(f"\n📊 Graph build complete:")
        print(f"   New edges discovered: {new_edges}")
        print(f"   Cached edges: {cached_edges}")
        print(f"   Rejected candidates: {skipped}")
        print(f"   Total valid connections: {len(self.edges)}")

    def _evaluate_edge(self, src_server, src_tool, src_profile,
                       tgt_server, tgt_tool, tgt_profile) -> GraphEdge:
        """Ask AI to evaluate the connection between two tools."""

        src_summary = src_profile.plain_language_summary if src_profile else "unknown"
        tgt_summary = tgt_profile.plain_language_summary if tgt_profile else "unknown"

        prompt = f"""You are evaluating whether the output of one MCP tool can feed into the input of another.

SOURCE TOOL:
- Server: {src_server}
- Tool: {src_tool.name}
- Description: {src_tool.description}
- Server summary: {src_summary}
- Input schema: {json.dumps(src_tool.input_schema, indent=2)}

TARGET TOOL:
- Server: {tgt_server}
- Tool: {tgt_tool.name}
- Description: {tgt_tool.description}
- Server summary: {tgt_summary}
- Input schema: {json.dumps(tgt_tool.input_schema, indent=2)}

Can the output of the SOURCE tool meaningfully feed into the input of the TARGET tool?

Return JSON in EXACTLY this format, nothing else:
{{
    "compatibility_type": "direct or translatable or incompatible",
    "confidence": 0.85,
    "translation_hint": "brief description of what mapping is needed, or empty string if direct or incompatible"
}}

Rules:
- "direct" means output fields map to input fields with minimal renaming
- "translatable" means data is semantically related but needs transformation
- "incompatible" means output has nothing useful for the input
- confidence is 0.0 to 1.0
"""

        raw = ask_gemini(prompt)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {
                "compatibility_type": "incompatible",
                "confidence": 0.0,
                "translation_hint": "",
            }

        return GraphEdge(
            source_server=src_server,
            source_tool=src_tool.name,
            target_server=tgt_server,
            target_tool=tgt_tool.name,
            compatibility_type=parsed.get("compatibility_type", "incompatible"),
            confidence=parsed.get("confidence", 0.0),
            translation_hint=parsed.get("translation_hint", ""),
        )

    def get_edges_from(self, server_name: str, tool_name: str = None) -> list[GraphEdge]:
        if tool_name:
            return [e for e in self.edges
                    if e.source_server == server_name and e.source_tool == tool_name]
        return [e for e in self.edges if e.source_server == server_name]

    def get_edges_to(self, server_name: str, tool_name: str = None) -> list[GraphEdge]:
        if tool_name:
            return [e for e in self.edges
                    if e.target_server == server_name and e.target_tool == tool_name]
        return [e for e in self.edges if e.target_server == server_name]

    def find_path(self, source_server: str, target_server: str, max_hops: int = 5) -> list[GraphEdge]:
        from collections import deque
        if source_server == target_server:
            return []
        queue = deque([(source_server, [])])
        visited = {source_server}
        while queue:
            current, path = queue.popleft()
            for edge in self.get_edges_from(current):
                if edge.target_server == target_server:
                    return path + [edge]
                if edge.target_server not in visited and len(path) < max_hops:
                    visited.add(edge.target_server)
                    queue.append((edge.target_server, path + [edge]))
        return []

    def display(self):
        print("\n📊 CAPABILITY GRAPH:")
        print("=" * 60)
        if not self.edges:
            print("   (empty — no connections found)")
            return
        for edge in sorted(self.edges, key=lambda e: -e.confidence):
            symbol = "✅" if edge.compatibility_type == "direct" else "🔄"
            print(f"   {symbol} {edge.source_server}.{edge.source_tool}")
            print(f"      → {edge.target_server}.{edge.target_tool}")
            print(f"      Type: {edge.compatibility_type} | Confidence: {edge.confidence}")
            if edge.translation_hint:
                print(f"      Hint: {edge.translation_hint}")
            print()

    def get_stats(self) -> dict:
        stats = {
            "total_edges": len(self.edges),
            "direct_edges": sum(1 for e in self.edges if e.compatibility_type == "direct"),
            "translatable_edges": sum(1 for e in self.edges if e.compatibility_type == "translatable"),
            "avg_confidence": sum(e.confidence for e in self.edges) / len(self.edges) if self.edges else 0,
        }
        stats.update(self.embedding_index.get_stats())
        return stats
