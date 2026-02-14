"""
NEXUS REST API
==============
FastAPI-based HTTP interface for NEXUS operations.
"""

import asyncio
import sys
import os
from typing import Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph
from nexus_core.discovery import DiscoveryEngine
from nexus_core.executor import PipelineExecutor
from nexus_core import database as db


# Global instances
registry: Registry = None
graph: CapabilityGraph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load state on startup."""
    global registry, graph
    print("🚀 Starting NEXUS API...")
    registry = Registry(use_cache=True)
    graph = CapabilityGraph(use_cache=True)
    print(f"   Loaded {len(registry.servers)} servers, {len(graph.edges)} edges")
    yield
    print("👋 Shutting down NEXUS API...")


app = FastAPI(
    title="NEXUS API",
    description="The Intelligent MCP Broker — REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router with /api prefix (frontend expects all endpoints under /api/)
api_router = APIRouter(prefix="/api")


# =============================================================================
# Request/Response Models
# =============================================================================

class ServerRegistration(BaseModel):
    name: str = Field(..., description="Server name (e.g., 'web-fetcher')")
    command: str = Field(..., description="Command to run server (e.g., 'uv')")
    args: list[str] = Field(..., description="Arguments (e.g., ['run', 'python', 'server.py'])")


class PipelineRequest(BaseModel):
    request: str = Field(..., description="Natural language request")
    url: Optional[str] = Field(None, description="URL to fetch (if needed)")
    channel: Optional[str] = Field("#team-updates", description="Slack channel")
    source_language: Optional[str] = Field(None, description="Source language for translation")
    target_language: Optional[str] = Field(None, description="Target language for translation")


class DiscoverRequest(BaseModel):
    request: str = Field(..., description="Natural language request to plan")


# =============================================================================
# Health & Status
# =============================================================================

@app.get("/")
async def app_root():
    return {"service": "NEXUS", "status": "healthy", "docs": "/docs"}

@api_router.get("/")
async def root():
    """API root — health check."""
    return {
        "service": "NEXUS API",
        "status": "healthy",
        "version": "1.0.0",
    }


@api_router.get("/status")
async def get_status():
    """Get NEXUS system status."""
    stats = db.get_stats()
    return {
        "status": "ready" if stats["servers"] > 0 else "empty",
        "servers": stats["servers"],
        "tools": stats["tools"],
        "edges": stats["edges"],
        "direct_edges": stats["direct_edges"],
        "translatable_edges": stats["translatable_edges"],
        "pipeline_runs": stats["pipeline_runs"],
    }


# =============================================================================
# Server Management
# =============================================================================

@api_router.get("/servers")
async def list_servers():
    """List all registered MCP servers."""
    servers = []
    for name, record in registry.servers.items():
        profile = record.semantic_profile
        servers.append({
            "name": name,
            "status": record.status,
            "summary": profile.plain_language_summary if profile else None,
            "domain": profile.domain if profile else None,
            "tags": profile.capability_tags if profile else [],
            "tools": [t.name for t in record.tools],
        })
    return {"total": len(servers), "servers": servers}


@api_router.post("/servers/register")
async def register_server(req: ServerRegistration, background_tasks: BackgroundTasks):
    """Register a new MCP server."""
    try:
        record = await registry.register(req.name, req.command, req.args)
        
        # Rebuild graph in background
        background_tasks.add_task(rebuild_graph)
        
        return {
            "status": "registered",
            "name": record.name,
            "summary": record.semantic_profile.plain_language_summary if record.semantic_profile else None,
            "tools": [t.name for t in record.tools],
            "message": "Server registered. Graph rebuild started in background.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/servers/{name}")
async def unregister_server(name: str):
    """Remove a server from NEXUS."""
    if name not in registry.servers:
        raise HTTPException(status_code=404, detail=f"Server '{name}' not found")
    
    success = registry.unregister(name)
    return {"status": "removed" if success else "failed", "name": name}


async def rebuild_graph():
    """Rebuild the capability graph (background task)."""
    global graph
    graph = CapabilityGraph(use_cache=False)
    graph.build_edges(registry.servers, incremental=True)


# =============================================================================
# Graph Operations
# =============================================================================

@api_router.get("/graph")
async def get_graph():
    """Get the capability graph."""
    edges = []
    for edge in sorted(graph.edges, key=lambda e: -e.confidence):
        edges.append({
            "source": f"{edge.source_server}.{edge.source_tool}",
            "target": f"{edge.target_server}.{edge.target_tool}",
            "type": edge.compatibility_type,
            "confidence": edge.confidence,
            "hint": edge.translation_hint,
        })
    return {
        "total_edges": len(edges),
        "edges": edges,
    }


@api_router.post("/graph/rebuild")
async def trigger_rebuild(background_tasks: BackgroundTasks):
    """Trigger a graph rebuild."""
    background_tasks.add_task(rebuild_graph)
    return {"status": "rebuild_started", "message": "Graph rebuild started in background."}


# =============================================================================
# Pipeline Operations
# =============================================================================

@api_router.post("/discover")
async def discover_pipeline(req: DiscoverRequest):
    """Discover a pipeline from natural language (without executing)."""
    if not registry.servers:
        raise HTTPException(status_code=400, detail="No servers registered")
    
    if not graph.edges:
        raise HTTPException(status_code=400, detail="Graph is empty. Register servers first.")
    
    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(req.request)
    
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
        "request": req.request,
        "confidence": pipeline.confidence,
        "steps": steps,
    }


@api_router.post("/execute")
async def execute_pipeline(req: PipelineRequest):
    """Discover and execute a pipeline."""
    if not registry.servers:
        raise HTTPException(status_code=400, detail="No servers registered")
    
    if not graph.edges:
        raise HTTPException(status_code=400, detail="Graph is empty")
    
    # Extract URL from request text if not provided in form
    url = req.url
    if not url:
        import re
        # Try to find explicit URLs
        url_match = re.search(r'https?://[^\s,]+', req.request)
        if url_match:
            url = url_match.group(0)
        else:
            # Try to find domain-like patterns (e.g., "CNN.com", "example.org")
            domain_match = re.search(r'\b([a-zA-Z0-9-]+\.(com|org|net|io|dev|co|ai|news))\b', req.request)
            if domain_match:
                url = f"https://{domain_match.group(1)}"
    
    # Build full request
    full_request = req.request
    if url and "fetch" not in req.request.lower():
        full_request = f"Fetch content from {url}, then {req.request}"
    
    # Build context
    context = {"channel": req.channel or "#team-updates"}
    if req.source_language:
        context["source_language"] = req.source_language
    if req.target_language:
        context["target_language"] = req.target_language
    
    # Build initial input
    initial_input = {}
    if url:
        initial_input["url"] = url
    
    # Discover pipeline
    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(full_request)
    
    # Execute
    executor = PipelineExecutor(registry.servers)
    results = await executor.execute(pipeline, initial_input, context, )
    
    # Format response
    step_results = []
    for r in results:
        step_results.append({
            "server": r.step.server_name,
            "tool": r.step.tool_name,
            "success": r.success,
            "duration": round(r.duration, 2),
            "error": r.error,
            "output": r.output_data if r.success else None,
        })
    
    all_success = all(r.success for r in results)
    total_time = sum(r.duration for r in results)
    final_output = results[-1].output_data if results else {}
    
    return {
        "request": req.request,
        "confidence": pipeline.confidence,
        "success": all_success,
        "total_duration": round(total_time, 2),
        "steps": step_results,
        "final_output": final_output,
    }


# =============================================================================
# Pipeline History
# =============================================================================

@api_router.get("/history")
async def get_pipeline_history(limit: int = 20):
    """Get recent pipeline execution history."""
    history = db.get_pipeline_history(limit=limit)
    return {"total": len(history), "runs": history}


# =============================================================================
# Run Server
# =============================================================================

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
