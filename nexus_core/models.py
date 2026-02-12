from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class ToolInfo(BaseModel):
    """Raw metadata about a single tool from an MCP server."""
    name: str
    description: str = ""
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)


class SemanticProfile(BaseModel):
    """AI-generated semantic understanding of an MCP server."""
    plain_language_summary: str = ""
    capability_tags: list[str] = Field(default_factory=list)
    input_concepts: list[str] = Field(default_factory=list)
    output_concepts: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    compatible_with: list[str] = Field(default_factory=list)
    domain: str = ""


class ServerRecord(BaseModel):
    """Complete record of a registered MCP server."""
    name: str
    transport_type: str = "stdio"
    command: str = ""
    args: list[str] = Field(default_factory=list)
    tools: list[ToolInfo] = Field(default_factory=list)
    semantic_profile: Optional[SemanticProfile] = None
    status: str = "registered"  # registered, profiled, healthy, offline
    registered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class GraphEdge(BaseModel):
    """A connection between two tools in the capability graph."""
    source_server: str
    source_tool: str
    target_server: str
    target_tool: str
    compatibility_type: str = "unknown"  # direct, translatable, incompatible
    confidence: float = 0.0
    translation_hint: str = ""
