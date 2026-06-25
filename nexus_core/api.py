"""
NEXUS REST API
==============
FastAPI-based HTTP interface for NEXUS operations.
"""

import asyncio
import sys
import os
import time
import platform
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, APIRouter, Depends, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field, validator

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph
from nexus_core.discovery import DiscoveryEngine
from nexus_core.executor import PipelineExecutor
from nexus_core import database as db


# =============================================================================
# Security — API Key Auth
# =============================================================================

_API_KEY = os.getenv("NEXUS_API_KEY", "")
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Security(_API_KEY_HEADER)):
    """Dependency that enforces API key on every protected route."""
    if not _API_KEY:
        # Key not configured — block all requests so misconfiguration is obvious
        raise HTTPException(status_code=500, detail="Server misconfiguration: NEXUS_API_KEY not set")
    if api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


# =============================================================================
# Rate Limiter — token bucket per IP
# =============================================================================

_RATE_LIMIT_RPM = int(os.getenv("NEXUS_RATE_LIMIT_RPM", "20"))   # requests per minute
_rate_buckets: dict = defaultdict(list)

def _check_rate_limit(request: Request):
    """Allow max NEXUS_RATE_LIMIT_RPM calls per minute per IP."""
    ip = request.client.host
    now = time.time()

    # Clean up current IP's bucket and check limit
    window = [t for t in _rate_buckets[ip] if now - t < 60]
    if len(window) >= _RATE_LIMIT_RPM:
        # Prevent timing side-channel analysis by returning a static Retry-After interval
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded — try again in a minute",
            headers={"Retry-After": "60"}
        )

    window.append(now)
    _rate_buckets[ip] = window


async def _rate_limit_gc_loop():
    """Background coroutine: prunes stale IP buckets every 60 seconds.
    Replaces the risky 100-request manual GC counter that allowed memory
    exhaustion by stopping at exactly the 99th request.
    """
    while True:
        await asyncio.sleep(60)
        now = time.time()
        expired = [ip for ip, timestamps in list(_rate_buckets.items())
                   if not any(now - t < 60 for t in timestamps)]
        for ip in expired:
            _rate_buckets.pop(ip, None)


# Allowlist of safe executables for MCP server commands
_COMMAND_ALLOWLIST = {"uv", "python", "python3", "node", "npx", "uvx"}


# Global instances
registry: Registry = None
graph: CapabilityGraph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load state on startup, clean up on shutdown."""
    global registry, graph
    print("🚀 Starting NEXUS API...")
    registry = Registry(use_cache=True)
    graph = CapabilityGraph(use_cache=True)
    print(f"   Loaded {len(registry.servers)} servers, {len(graph.edges)} edges")

    # Start background rate-limiter GC task (replaces risky 100-request counter)
    gc_task = asyncio.create_task(_rate_limit_gc_loop())

    yield

    # Cancel the background GC task cleanly on shutdown
    gc_task.cancel()
    try:
        await gc_task
    except asyncio.CancelledError:
        pass
    print("👋 Shutting down NEXUS API...")


app = FastAPI(
    title="NEXUS API",
    description="The Intelligent MCP Broker — REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — restrict to known UI origins (set CORS_ORIGINS env var for production)
_cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# API Router with /api prefix (frontend expects all endpoints under /api/)
api_router = APIRouter(prefix="/api", dependencies=[Depends(require_api_key)])


# =============================================================================
# Request/Response Models
# =============================================================================

class ServerRegistration(BaseModel):
    name: str = Field(..., description="Server name (e.g., 'web-fetcher')")
    command: str = Field(..., description="Command to run server (e.g., 'uv')")
    args: list[str] = Field(..., description="Arguments (e.g., ['run', 'python', 'server.py'])")

    @validator("command")
    def command_must_be_safe(cls, v):
        """Reject commands not on the allowlist to prevent RCE and directory traversal."""
        # Block path separators and drive letters to prevent custom executable path hijacking
        if "/" in v or "\\" in v or ":" in v:
            raise ValueError("Command must not contain path separators or drive letters.")
        
        # Check against allowlist (removing .exe suffix if present)
        base_cmd = v.lower()
        if base_cmd.endswith(".exe"):
            base_cmd = base_cmd[:-4]
            
        if base_cmd not in _COMMAND_ALLOWLIST:
            raise ValueError(
                f"Command '{v}' is not allowed. Permitted commands: {sorted(_COMMAND_ALLOWLIST)}"
            )
        return v

    @validator("args")
    def args_must_be_safe(cls, v):
        """Reject dangerous arguments containing shell metacharacters or execution flags."""
        dangerous_chars = {";", "&", "|", "$", "`", "\n", "\r", "<", ">", "(", ")"}
        dangerous_flags = {"-c", "-m", "-e", "--eval", "eval", "exec"}
        
        for arg in v:
            # Check for shell metacharacters
            if any(char in arg for char in dangerous_chars):
                raise ValueError(f"Argument '{arg}' contains dangerous shell characters.")
            
            # Check for python/node execution flags
            if arg.lower() in dangerous_flags:
                raise ValueError(f"Argument '{arg}' contains a forbidden execution flag.")
                
            # Prevent directory traversal in args
            if ".." in arg:
                raise ValueError(f"Argument '{arg}' contains directory traversal '..'.")
        return v


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

_START_TIME = time.time()

def _format_duration(seconds: float) -> str:
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    return f"{s}s"

@app.get("/health")
async def health_check():
    """Detailed health check for production environment."""
    uptime_sec = time.time() - _START_TIME
    
    # Process memory
    proc_mem = "unknown"
    try:
        pid = os.getpid()
        out = os.popen(f'wmic process where ProcessId={pid} get WorkingSetSize /Value').read()
        for line in out.splitlines():
            if "WorkingSetSize" in line:
                bytes_used = int(line.split("=", 1)[1].strip())
                proc_mem = f"{round(bytes_used / 1024 / 1024, 2)} MB"
    except Exception:
        pass

    # System memory
    sys_mem = {"total": "unknown", "free": "unknown", "used": "unknown"}
    try:
        out = os.popen('wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value').read()
        lines = [line.strip() for line in out.splitlines() if "=" in line]
        data = dict(line.split("=", 1) for line in lines)
        free_kb = int(data.get("FreePhysicalMemory", 0))
        total_kb = int(data.get("TotalVisibleMemorySize", 0))
        used_kb = total_kb - free_kb
        sys_mem = {
            "total": f"{round(total_kb / 1024 / 1024, 2)} GB",
            "free": f"{round(free_kb / 1024 / 1024, 2)} GB",
            "used": f"{round(used_kb / 1024 / 1024, 2)} GB"
        }
    except Exception:
        pass

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat() if hasattr(timezone, "utc") else datetime.utcnow().isoformat() + "Z",
        "uptime": {
            "seconds": int(uptime_sec),
            "formatted": _format_duration(uptime_sec),
        },
        "server": {
            "pythonVersion": platform.python_version(),
            "platform": platform.system(),
            "arch": platform.machine(),
            "cpus": os.cpu_count(),
            "memory": {
                "processMemory": proc_mem
            },
            "systemMemory": sys_mem
        },
        "environment": os.getenv("NODE_ENV", "production")
    }

@app.get("/health/simple")
async def health_simple():
    """Simple text response for load balancers."""
    return "OK"

@app.get("/health/ready")
async def health_ready():
    """Readiness probe checking registry and graph initialization."""
    is_ready = registry is not None and graph is not None
    if is_ready:
        return {"ready": True, "state": "success"}
    else:
        raise HTTPException(
            status_code=503,
            detail={"ready": False, "state": "initializing", "reason": "Registry or graph not initialized"}
        )

@app.get("/health/live")
async def health_live():
    """Liveness probe indicating process is active."""
    return {"alive": True, "timestamp": datetime.now(timezone.utc).isoformat() if hasattr(timezone, "utc") else datetime.utcnow().isoformat() + "Z"}

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
async def trigger_rebuild(request: Request, background_tasks: BackgroundTasks):
    """Trigger a graph rebuild — rate limited."""
    _check_rate_limit(request)
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
async def execute_pipeline(req: PipelineRequest, request: Request):
    _check_rate_limit(request)
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
    try:
        engine = DiscoveryEngine(registry.servers, graph.edges)
        pipeline = engine.discover(full_request)
    except Exception as e:
        return {
            "request": req.request,
            "confidence": 0,
            "success": False,
            "total_duration": 0,
            "steps": [],
            "final_output": {"error": f"Could not plan pipeline: {str(e)}"},
        }
    
    # Execute
    pipeline_steps_meta = [{"server": s.server_name, "tool": s.tool_name} for s in pipeline.steps]
    run_id = await asyncio.to_thread(
        db.save_pipeline_run, req.request, pipeline_steps_meta, context
    )

    try:
        executor = PipelineExecutor(registry.servers)
        results = await executor.execute(pipeline, initial_input, context, )
    except Exception as e:
        await asyncio.to_thread(
            db.update_pipeline_run, run_id, "failed", {"error": str(e)}, 0
        )
        return {
            "request": req.request,
            "confidence": pipeline.confidence,
            "success": False,
            "total_duration": 0,
            "steps": [],
            "final_output": {"error": f"Execution error: {str(e)}"},
        }
    
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

    # Save to history
    history_result = {
        "steps": step_results,
        "final_output": final_output,
        "confidence": pipeline.confidence
    }

    await asyncio.to_thread(
        db.update_pipeline_run,
        run_id,
        "completed" if all_success else "partial",
        history_result,
        round(total_time, 2)
    )
    
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
async def get_pipeline_history(
    limit: int = 20,
    offset: int = 0,
):
    """Get paginated pipeline execution history.

    Query params:
      - limit: max records to return (1–100, default 20)
      - offset: number of records to skip (default 0)
    """
    limit = max(1, min(limit, 100))   # clamp between 1 and 100
    offset = max(0, offset)
    history = await asyncio.to_thread(db.get_pipeline_history, limit, offset)
    return {"total": len(history), "limit": limit, "offset": offset, "runs": history}


# =============================================================================
# Run Server
# =============================================================================

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
