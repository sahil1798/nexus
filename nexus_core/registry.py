"""
NEXUS Registry with Database Persistence
=========================================
Manages MCP server registration with persistent storage.
"""

import asyncio
import json
import sys
sys.path.insert(0, '.')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nexus_core.models import ServerRecord, ToolInfo
from nexus_core.profiler import profile_server
from nexus_core import database as db


class Registry:
    """Manages registration and profiling of MCP servers with persistence."""

    def __init__(self, use_cache: bool = True):
        """
        Initialize the registry.
        
        Args:
            use_cache: If True, load existing servers from database on init.
        """
        self.servers: dict[str, ServerRecord] = {}
        self.use_cache = use_cache
        
        if use_cache:
            self._load_from_database()

    def _load_from_database(self):
        """Load all servers from database into memory."""
        self.servers = db.load_all_servers()
        if self.servers:
            print(f"📦 Loaded {len(self.servers)} servers from database")

    async def register(self, name: str, command: str, args: list[str], force_refresh: bool = False) -> ServerRecord:
        """
        Register an MCP server. Connects to it, reads tools, profiles with AI.
        
        Args:
            name: Server name
            command: Command to run the server
            args: Arguments for the command
            force_refresh: If True, re-register even if server exists in DB
        """
        # Check if already in database and not forcing refresh
        if not force_refresh and db.server_exists(name):
            cached = db.load_server(name)
            if cached:
                print(f"📦 Server '{name}' loaded from database (cached)")
                self.servers[name] = cached
                return cached

        print(f"\n{'='*60}")
        print(f"📡 Connecting to '{name}'...")

        server_params = StdioServerParameters(
            command=command,
            args=args,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_response = await session.list_tools()

                tools = []
                for tool in tools_response.tools:
                    tool_schema = ToolInfo(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema if tool.inputSchema else {},
                    )
                    tools.append(tool_schema)
                    print(f"   🔧 Found tool: {tool.name}")

        # Create server record
        record = ServerRecord(
            name=name,
            command=command,
            args=args,
            tools=tools,
        )

        # Profile with AI
        print(f"🧠 Analyzing capabilities of '{name}'...")
        profile = profile_server(name, tools)
        record.semantic_profile = profile
        record.status = "profiled"

        # Save to database
        db.save_server(record)

        # Store in memory
        self.servers[name] = record

        # Display results
        print(f"✅ Server '{name}' registered and profiled!")
        print(f"   Summary: {profile.plain_language_summary}")
        print(f"   Tags: {', '.join(profile.capability_tags)}")
        print(f"   Domain: {profile.domain}")

        # Check for potential connections
        self._check_connections(name)

        return record

    def _check_connections(self, new_server_name: str):
        """Check if the new server has potential connections with existing servers."""
        new_server = self.servers[new_server_name]
        if not new_server.semantic_profile:
            return

        new_tags = set(new_server.semantic_profile.capability_tags)
        new_compatible = set(new_server.semantic_profile.compatible_with)

        for existing_name, existing_record in self.servers.items():
            if existing_name == new_server_name:
                continue
            if not existing_record.semantic_profile:
                continue

            existing_tags = set(existing_record.semantic_profile.capability_tags)

            tag_overlap = new_tags & existing_tags
            compatible_mention = any(
                existing_name.lower() in c.lower() or
                any(t.lower() in c.lower() for t in existing_tags)
                for c in new_compatible
            )

            if tag_overlap or compatible_mention:
                print(f"   🔗 NOTE: Can potentially chain with '{existing_name}'")

    def get_server(self, name: str) -> ServerRecord | None:
        """Get a server by name, checking memory first then database."""
        if name in self.servers:
            return self.servers[name]
        
        # Try loading from database
        server = db.load_server(name)
        if server:
            self.servers[name] = server
            return server
        
        return None

    def list_servers(self) -> list[ServerRecord]:
        """Return all registered servers."""
        return list(self.servers.values())

    def unregister(self, name: str) -> bool:
        """Remove a server from registry and database."""
        if name in self.servers:
            del self.servers[name]
        
        # Also delete associated edges
        db.delete_edges_for_server(name)
        
        return db.delete_server(name)

    def reload_from_database(self):
        """Force reload all servers from database."""
        self.servers = db.load_all_servers()
        print(f"🔄 Reloaded {len(self.servers)} servers from database")

    def get_stats(self) -> dict:
        """Get registry statistics."""
        stats = db.get_stats()
        stats["in_memory_servers"] = len(self.servers)
        return stats
