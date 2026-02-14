"""
NEXUS Database Layer
====================
SQLite-based persistence for servers, tools, edges, and pipelines.
Eliminates in-memory-only limitation.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Optional
from contextlib import contextmanager

from nexus_core.models import ServerRecord, ToolInfo, SemanticProfile, GraphEdge


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nexus.db")


def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = os.path.dirname(DB_PATH)
    os.makedirs(data_dir, exist_ok=True)


@contextmanager
def get_connection():
    """Context manager for database connections."""
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize the database schema."""
    with get_connection() as conn:
        # Servers table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                name TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                args TEXT NOT NULL,
                status TEXT DEFAULT 'registered',
                registered_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # Tools table (one-to-many with servers)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                input_schema TEXT,
                output_schema TEXT,
                FOREIGN KEY (server_name) REFERENCES servers(name) ON DELETE CASCADE,
                UNIQUE(server_name, name)
            )
        """)
        
        # Semantic profiles table (one-to-one with servers)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_profiles (
                server_name TEXT PRIMARY KEY,
                plain_language_summary TEXT,
                capability_tags TEXT,
                input_concepts TEXT,
                output_concepts TEXT,
                use_cases TEXT,
                compatible_with TEXT,
                domain TEXT,
                embedding TEXT,
                FOREIGN KEY (server_name) REFERENCES servers(name) ON DELETE CASCADE
            )
        """)
        
        # Graph edges table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_server TEXT NOT NULL,
                source_tool TEXT NOT NULL,
                target_server TEXT NOT NULL,
                target_tool TEXT NOT NULL,
                compatibility_type TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                translation_hint TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_server) REFERENCES servers(name) ON DELETE CASCADE,
                FOREIGN KEY (target_server) REFERENCES servers(name) ON DELETE CASCADE,
                UNIQUE(source_server, source_tool, target_server, target_tool)
            )
        """)
        
        # Translation specs cache table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS translation_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                edge_id INTEGER NOT NULL,
                spec TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (edge_id) REFERENCES edges(id) ON DELETE CASCADE
            )
        """)
        
        # Pipeline history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request TEXT NOT NULL,
                pipeline_steps TEXT NOT NULL,
                context TEXT,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                total_duration REAL,
                result TEXT
            )
        """)
        
        # Create indexes for faster queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_server ON tools(server_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_server, source_tool)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_server, target_tool)")
        
    print("✅ Database initialized at:", DB_PATH)


# =============================================================================
# Server CRUD Operations
# =============================================================================

def save_server(record: ServerRecord) -> None:
    """Save or update a server record."""
    with get_connection() as conn:
        now = datetime.now(timezone.utc).isoformat()
        
        # Upsert server
        conn.execute("""
            INSERT INTO servers (name, command, args, status, registered_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                command = excluded.command,
                args = excluded.args,
                status = excluded.status,
                updated_at = ?
        """, (
            record.name,
            record.command,
            json.dumps(record.args),
            record.status,
            record.registered_at,
            now,
            now
        ))
        
        # Delete old tools and insert new ones
        conn.execute("DELETE FROM tools WHERE server_name = ?", (record.name,))
        for tool in record.tools:
            conn.execute("""
                INSERT INTO tools (server_name, name, description, input_schema, output_schema)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record.name,
                tool.name,
                tool.description,
                json.dumps(tool.input_schema),
                json.dumps(tool.output_schema)
            ))
        
        # Save semantic profile if exists
        if record.semantic_profile:
            profile = record.semantic_profile
            conn.execute("""
                INSERT INTO semantic_profiles 
                (server_name, plain_language_summary, capability_tags, input_concepts,
                 output_concepts, use_cases, compatible_with, domain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(server_name) DO UPDATE SET
                    plain_language_summary = excluded.plain_language_summary,
                    capability_tags = excluded.capability_tags,
                    input_concepts = excluded.input_concepts,
                    output_concepts = excluded.output_concepts,
                    use_cases = excluded.use_cases,
                    compatible_with = excluded.compatible_with,
                    domain = excluded.domain
            """, (
                record.name,
                profile.plain_language_summary,
                json.dumps(profile.capability_tags),
                json.dumps(profile.input_concepts),
                json.dumps(profile.output_concepts),
                json.dumps(profile.use_cases),
                json.dumps(profile.compatible_with),
                profile.domain
            ))


def load_server(name: str) -> Optional[ServerRecord]:
    """Load a server record by name."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM servers WHERE name = ?", (name,)
        ).fetchone()
        
        if not row:
            return None
        
        # Load tools
        tool_rows = conn.execute(
            "SELECT * FROM tools WHERE server_name = ?", (name,)
        ).fetchall()
        
        tools = [
            ToolInfo(
                name=t['name'],
                description=t['description'] or "",
                input_schema=json.loads(t['input_schema']) if t['input_schema'] else {},
                output_schema=json.loads(t['output_schema']) if t['output_schema'] else {}
            )
            for t in tool_rows
        ]
        
        # Load semantic profile
        profile_row = conn.execute(
            "SELECT * FROM semantic_profiles WHERE server_name = ?", (name,)
        ).fetchone()
        
        profile = None
        if profile_row:
            profile = SemanticProfile(
                plain_language_summary=profile_row['plain_language_summary'] or "",
                capability_tags=json.loads(profile_row['capability_tags']) if profile_row['capability_tags'] else [],
                input_concepts=json.loads(profile_row['input_concepts']) if profile_row['input_concepts'] else [],
                output_concepts=json.loads(profile_row['output_concepts']) if profile_row['output_concepts'] else [],
                use_cases=json.loads(profile_row['use_cases']) if profile_row['use_cases'] else [],
                compatible_with=json.loads(profile_row['compatible_with']) if profile_row['compatible_with'] else [],
                domain=profile_row['domain'] or ""
            )
        
        return ServerRecord(
            name=row['name'],
            command=row['command'],
            args=json.loads(row['args']),
            tools=tools,
            semantic_profile=profile,
            status=row['status'],
            registered_at=row['registered_at']
        )


def load_all_servers() -> dict[str, ServerRecord]:
    """Load all server records."""
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM servers").fetchall()
        
    servers = {}
    for row in rows:
        server = load_server(row['name'])
        if server:
            servers[server.name] = server
    
    return servers


def delete_server(name: str) -> bool:
    """Delete a server and all related data."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM servers WHERE name = ?", (name,))
        return cursor.rowcount > 0


def server_exists(name: str) -> bool:
    """Check if a server exists."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM servers WHERE name = ?", (name,)
        ).fetchone()
        return row is not None


# =============================================================================
# Edge CRUD Operations
# =============================================================================

def save_edge(edge: GraphEdge) -> int:
    """Save an edge to the database. Returns the edge ID."""
    with get_connection() as conn:
        now = datetime.now(timezone.utc).isoformat()
        
        cursor = conn.execute("""
            INSERT INTO edges 
            (source_server, source_tool, target_server, target_tool, 
             compatibility_type, confidence, translation_hint, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_server, source_tool, target_server, target_tool) DO UPDATE SET
                compatibility_type = excluded.compatibility_type,
                confidence = excluded.confidence,
                translation_hint = excluded.translation_hint
        """, (
            edge.source_server,
            edge.source_tool,
            edge.target_server,
            edge.target_tool,
            edge.compatibility_type,
            edge.confidence,
            edge.translation_hint,
            now
        ))
        
        return cursor.lastrowid


def load_all_edges() -> list[GraphEdge]:
    """Load all edges from the database."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM edges").fetchall()
        
    return [
        GraphEdge(
            source_server=row['source_server'],
            source_tool=row['source_tool'],
            target_server=row['target_server'],
            target_tool=row['target_tool'],
            compatibility_type=row['compatibility_type'],
            confidence=row['confidence'],
            translation_hint=row['translation_hint'] or ""
        )
        for row in rows
    ]


def load_edges_from_server(server_name: str) -> list[GraphEdge]:
    """Load all edges originating from a server."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM edges WHERE source_server = ?", (server_name,)
        ).fetchall()
        
    return [
        GraphEdge(
            source_server=row['source_server'],
            source_tool=row['source_tool'],
            target_server=row['target_server'],
            target_tool=row['target_tool'],
            compatibility_type=row['compatibility_type'],
            confidence=row['confidence'],
            translation_hint=row['translation_hint'] or ""
        )
        for row in rows
    ]


def load_edges_to_server(server_name: str) -> list[GraphEdge]:
    """Load all edges pointing to a server."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM edges WHERE target_server = ?", (server_name,)
        ).fetchall()
        
    return [
        GraphEdge(
            source_server=row['source_server'],
            source_tool=row['source_tool'],
            target_server=row['target_server'],
            target_tool=row['target_tool'],
            compatibility_type=row['compatibility_type'],
            confidence=row['confidence'],
            translation_hint=row['translation_hint'] or ""
        )
        for row in rows
    ]


def edge_exists(source_server: str, source_tool: str, target_server: str, target_tool: str) -> bool:
    """Check if an edge already exists."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT 1 FROM edges 
            WHERE source_server = ? AND source_tool = ? 
            AND target_server = ? AND target_tool = ?
        """, (source_server, source_tool, target_server, target_tool)).fetchone()
        return row is not None


def delete_edges_for_server(server_name: str) -> int:
    """Delete all edges involving a server. Returns count deleted."""
    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM edges 
            WHERE source_server = ? OR target_server = ?
        """, (server_name, server_name))
        return cursor.rowcount


def clear_all_edges() -> int:
    """Clear all edges from the database."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM edges")
        return cursor.rowcount


# =============================================================================
# Pipeline Run Operations
# =============================================================================

def save_pipeline_run(request: str, steps: list, context: dict, status: str = "pending") -> int:
    """Save a pipeline run. Returns the run ID."""
    with get_connection() as conn:
        now = datetime.now(timezone.utc).isoformat()
        
        cursor = conn.execute("""
            INSERT INTO pipeline_runs (request, pipeline_steps, context, status, started_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request,
            json.dumps(steps),
            json.dumps(context),
            status,
            now
        ))
        
        return cursor.lastrowid


def update_pipeline_run(run_id: int, status: str, result: dict = None, duration: float = None):
    """Update a pipeline run status."""
    with get_connection() as conn:
        now = datetime.now(timezone.utc).isoformat()
        
        conn.execute("""
            UPDATE pipeline_runs
            SET status = ?, result = ?, total_duration = ?, completed_at = ?
            WHERE id = ?
        """, (status, json.dumps(result) if result else None, duration, now, run_id))


def get_pipeline_history(limit: int = 50) -> list[dict]:
    """Get recent pipeline runs with parsed JSON fields."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
    results = []
    for row in rows:
        d = dict(row)
        
        # Parse JSON fields
        if d.get('pipeline_steps'):
            try:
                d['steps'] = json.loads(d['pipeline_steps'])
            except:
                d['steps'] = []
                
        if d.get('result'):
            try:
                d['result'] = json.loads(d['result'])
                # Extract confidence if stored in result
                if isinstance(d['result'], dict):
                    d['confidence'] = d['result'].get('confidence', 0.0)
            except:
                d['result'] = {}
                
        if d.get('context'):
            try:
                d['context'] = json.loads(d['context'])
            except:
                d['context'] = {}
                
        # Map status to success boolean for frontend
        d['success'] = d['status'] == 'completed'
        
        results.append(d)
        
    return results


# =============================================================================
# Statistics
# =============================================================================

def get_stats() -> dict:
    """Get database statistics."""
    with get_connection() as conn:
        server_count = conn.execute("SELECT COUNT(*) FROM servers").fetchone()[0]
        tool_count = conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        pipeline_count = conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0]
        
        direct_edges = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE compatibility_type = 'direct'"
        ).fetchone()[0]
        
        translatable_edges = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE compatibility_type = 'translatable'"
        ).fetchone()[0]
        
    return {
        "servers": server_count,
        "tools": tool_count,
        "edges": edge_count,
        "direct_edges": direct_edges,
        "translatable_edges": translatable_edges,
        "pipeline_runs": pipeline_count
    }


# Initialize on import
init_database()
