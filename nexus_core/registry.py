import asyncio
import json
import sys
sys.path.insert(0, '.')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nexus_core.models import ServerRecord, ToolInfo
from nexus_core.profiler import profile_server


class Registry:
    """Manages registration and profiling of MCP servers."""

    def __init__(self):
        self.servers: dict[str, ServerRecord] = {}

    async def register(self, name: str, command: str, args: list[str]) -> ServerRecord:
        """
        Connect to an MCP server, read its tools, profile it with AI,
        and store the result.
        """
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
                    tool_info = ToolInfo(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema if tool.inputSchema else {},
                    )
                    tools.append(tool_info)
                    print(f"   🔧 Found tool: {tool.name}")

        record = ServerRecord(
            name=name,
            command=command,
            args=args,
            tools=tools,
        )

        print(f"🧠 Analyzing capabilities of '{name}'...")
        profile = profile_server(name, tools)
        record.semantic_profile = profile
        record.status = "profiled"

        self.servers[name] = record

        print(f"✅ Server '{name}' registered and profiled!")
        print(f"   Summary: {profile.plain_language_summary}")
        print(f"   Tags: {', '.join(profile.capability_tags)}")
        print(f"   Domain: {profile.domain}")

        self._check_connections(name)

        return record

    def _check_connections(self, new_server_name: str):
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

    def list_servers(self) -> list[ServerRecord]:
        return list(self.servers.values())

    def get_server(self, name: str) -> ServerRecord | None:
        return self.servers.get(name)
