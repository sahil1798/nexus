import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from nexus_core.models import ServerRecord, ToolInfo, SemanticProfile, GraphEdge
from nexus_core.discovery import DiscoveryEngine
from nexus_core.executor import PipelineExecutor

mcp = FastMCP("nexus")

# Global state
servers: dict[str, ServerRecord] = {}
edges: list[GraphEdge] = []


def load_state():
    """Load pre-built state from JSON file."""
    global servers, edges

    state_file = os.path.join(os.path.dirname(__file__), "..", "nexus_state.json")

    if not os.path.exists(state_file):
        print("⚠️  No saved state found. Run 'uv run python demo/setup_nexus.py' first.")
        return False

    with open(state_file, "r") as f:
        state = json.load(f)

    # Load servers
    for name, data in state["servers"].items():
        tools = [ToolInfo(**t) for t in data["tools"]]
        profile = SemanticProfile(**data["profile"])
        record = ServerRecord(
            name=data["name"],
            command=data["command"],
            args=data["args"],
            tools=tools,
            semantic_profile=profile,
            status="profiled",
        )
        servers[name] = record

    # Load edges
    for e in state["edges"]:
        edges.append(GraphEdge(**e))

    print(f"✅ Loaded {len(servers)} servers and {len(edges)} connections from saved state.")
    return True


# Load state on startup
load_state()


@mcp.tool()
def nexus_status() -> dict:
    """
    Get the current status of NEXUS.

    Returns:
        System status including registered servers and connections.
    """
    return {
        "servers_registered": len(servers),
        "total_connections": len(edges),
        "server_names": list(servers.keys()),
        "ready": len(servers) > 0 and len(edges) > 0,
    }


@mcp.tool()
def list_servers() -> dict:
    """
    List all MCP servers registered with NEXUS.

    Returns:
        All registered servers with their capabilities.
    """
    result = []
    for name, record in servers.items():
        result.append({
            "name": name,
            "summary": record.semantic_profile.plain_language_summary,
            "domain": record.semantic_profile.domain,
            "tools": [t.name for t in record.tools],
        })

    return {"total": len(result), "servers": result}


@mcp.tool()
def show_connections() -> dict:
    """
    Show all discovered connections between server tools.

    Returns:
        All edges in the capability graph with confidence scores.
    """
    result = []
    for edge in sorted(edges, key=lambda e: -e.confidence):
        result.append({
            "from": f"{edge.source_server}.{edge.source_tool}",
            "to": f"{edge.target_server}.{edge.target_tool}",
            "type": edge.compatibility_type,
            "confidence": edge.confidence,
        })

    return {"total": len(result), "connections": result}


@mcp.tool()
async def discover_pipeline(request: str) -> dict:
    """
    Given a natural language request, discover the optimal pipeline.
    Does NOT execute - just shows the plan.

    Args:
        request: What you want to accomplish
                 (e.g., "Fetch a webpage, summarize it, and post to Slack")

    Returns:
        The discovered pipeline with steps and confidence.
    """
    if not servers or not edges:
        return {"error": "NEXUS not initialized. Run setup_nexus.py first."}

    engine = DiscoveryEngine(servers, edges)
    pipeline = engine.discover(request)

    steps = []
    for i, step in enumerate(pipeline.steps):
        step_info = {
            "step": i + 1,
            "server": step.server_name,
            "tool": step.tool_name,
            "connection_type": step.edge.compatibility_type if step.edge else "entry_point",
        }
        if step.edge and step.edge.translation_hint:
            step_info["translation_hint"] = step.edge.translation_hint
        steps.append(step_info)

    return {
        "request": request,
        "confidence": pipeline.confidence,
        "steps": steps,
    }


@mcp.tool()
async def execute_pipeline(request: str, url: str = "", channel: str = "#team-updates") -> dict:
    """
    Discover AND execute a pipeline to fulfill a natural language request.
    Calls real MCP servers and returns results.

    Args:
        request: What you want to do
                 (e.g., "summarize it and post to slack")
        url: URL to fetch content from (if needed)
        channel: Slack channel to post to (default: #team-updates)

    Returns:
        Execution results including final output.
    """
    if not servers or not edges:
        return {"error": "NEXUS not initialized. Run setup_nexus.py first."}

    # Build full request
    full_request = request
    if url and "fetch" not in request.lower():
        full_request = f"Fetch content from {url}, then {request}"

    initial_input = {"url": url} if url else {}
    context = {"channel": channel}

    engine = DiscoveryEngine(servers, edges)
    pipeline = engine.discover(full_request)

    executor = PipelineExecutor(servers)
    results = await executor.execute(pipeline, initial_input, context)

    step_results = []
    for r in results:
        step_results.append({
            "server": r.step.server_name,
            "tool": r.step.tool_name,
            "success": r.success,
            "duration": f"{r.duration:.2f}s",
        })

    all_success = all(r.success for r in results)
    total_time = sum(r.duration for r in results)
    final_output = results[-1].output_data if results else {}

    return {
        "request": request,
        "all_succeeded": all_success,
        "total_time": f"{total_time:.2f}s",
        "steps": step_results,
        "final_output": final_output,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
