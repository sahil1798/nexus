"""
NEXUS Embedding Engine
======================
Uses Gemini embeddings + cosine similarity to find candidate
tool connections WITHOUT checking every pair with LLM calls.

O(N²) LLM calls → O(N) embedding calls + O(N²) cosine similarity (instant)
"""

import json
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, '.')

from nexus_core.config import gemini_client
from nexus_core.models import ServerRecord, ToolInfo


EMBEDDING_MODEL = "models/gemini-embedding-001"


def generate_output_text(server_name: str, tool: ToolInfo, profile_summary: str = "") -> str:
    """Create text focused on what a tool OUTPUTS."""
    parts = [
        f"This tool ({server_name}.{tool.name}) produces output.",
        f"Tool description: {tool.description}",
        f"Server context: {profile_summary}",
    ]
    if tool.output_schema:
        parts.append(f"Output schema: {json.dumps(tool.output_schema)}")
    else:
        parts.append(f"Output: derived from {tool.description}")
    return "\n".join(parts)


def generate_input_text(server_name: str, tool: ToolInfo, profile_summary: str = "") -> str:
    """Create text focused on what a tool NEEDS as input."""
    parts = [
        f"This tool ({server_name}.{tool.name}) requires input.",
        f"Tool description: {tool.description}",
        f"Server context: {profile_summary}",
    ]
    if tool.input_schema:
        parts.append(f"Input schema: {json.dumps(tool.input_schema)}")
    return "\n".join(parts)


def get_embedding(text: str) -> list[float]:
    """Get embedding vector from Gemini."""
    result = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return result.embeddings[0].values


class EmbeddingIndex:
    """
    Maintains embedding vectors for all tools.
    Enables fast similarity search for edge discovery.
    """

    def __init__(self):
        self.output_embeddings: dict[str, np.ndarray] = {}
        self.input_embeddings: dict[str, np.ndarray] = {}
        self.tool_keys: list[str] = []

    def index_server(self, server: ServerRecord):
        """Generate and store embeddings for all tools in a server."""
        profile_summary = ""
        if server.semantic_profile:
            profile_summary = server.semantic_profile.plain_language_summary

        for tool in server.tools:
            key = f"{server.name}.{tool.name}"

            if key in self.output_embeddings:
                continue

            print(f"   🔢 Generating embeddings for {key}...")

            output_text = generate_output_text(server.name, tool, profile_summary)
            output_vec = get_embedding(output_text)
            self.output_embeddings[key] = np.array(output_vec)

            input_text = generate_input_text(server.name, tool, profile_summary)
            input_vec = get_embedding(input_text)
            self.input_embeddings[key] = np.array(input_vec)

            if key not in self.tool_keys:
                self.tool_keys.append(key)

    def index_all_servers(self, servers: dict[str, ServerRecord]):
        """Index all servers."""
        print("\n🔢 Building embedding index...")
        for server in servers.values():
            self.index_server(server)
        print(f"   ✅ Indexed {len(self.tool_keys)} tools")

    def find_candidates(self, threshold: float = 0.5, top_k: int = 10) -> list[tuple[str, str, float]]:
        """
        Find candidate tool pairs by comparing output embeddings
        against input embeddings using cosine similarity.
        """
        if len(self.tool_keys) < 2:
            return []

        candidates = []

        for source_key in self.tool_keys:
            source_server = source_key.split(".")[0]
            source_vec = self.output_embeddings[source_key].reshape(1, -1)

            for target_key in self.tool_keys:
                target_server = target_key.split(".")[0]

                if source_server == target_server:
                    continue

                target_vec = self.input_embeddings[target_key].reshape(1, -1)
                sim = cosine_similarity(source_vec, target_vec)[0][0]

                if sim >= threshold:
                    candidates.append((source_key, target_key, float(sim)))

        candidates.sort(key=lambda x: -x[2])
        return candidates[:top_k * len(self.tool_keys)]

    def get_stats(self) -> dict:
        return {
            "indexed_tools": len(self.tool_keys),
            "output_embeddings": len(self.output_embeddings),
            "input_embeddings": len(self.input_embeddings),
        }
