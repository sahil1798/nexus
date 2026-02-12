import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph

async def main():
    print("=" * 60)
    print("NEXUS Setup - Building and Saving State")
    print("=" * 60)

    registry = Registry()

    # Register all servers
    print("\n📡 Registering servers...")
    await registry.register('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py'])
    await registry.register('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py'])
    await registry.register('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py'])
    await registry.register('sentiment-analyzer', 'uv', ['run', 'python', 'servers/sentiment-analyzer/server.py'])

    # Build graph
    print("\n📊 Building capability graph...")
    graph = CapabilityGraph()
    graph.build_from_servers(registry.list_servers())

    # Save state
    state = {
        "servers": {},
        "edges": [],
    }

    for name, record in registry.servers.items():
        state["servers"][name] = {
            "name": record.name,
            "command": record.command,
            "args": record.args,
            "tools": [{"name": t.name, "description": t.description, "input_schema": t.input_schema, "output_schema": t.output_schema} for t in record.tools],
            "profile": {
                "plain_language_summary": record.semantic_profile.plain_language_summary,
                "capability_tags": record.semantic_profile.capability_tags,
                "input_concepts": record.semantic_profile.input_concepts,
                "output_concepts": record.semantic_profile.output_concepts,
                "use_cases": record.semantic_profile.use_cases,
                "compatible_with": record.semantic_profile.compatible_with,
                "domain": record.semantic_profile.domain,
            }
        }

    for edge in graph.edges:
        state["edges"].append({
            "source_server": edge.source_server,
            "source_tool": edge.source_tool,
            "target_server": edge.target_server,
            "target_tool": edge.target_tool,
            "compatibility_type": edge.compatibility_type,
            "confidence": edge.confidence,
            "translation_hint": edge.translation_hint,
        })

    state_file = os.path.join(os.path.dirname(__file__), "..", "nexus_state.json")
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    print(f"\n✅ State saved to nexus_state.json")
    print(f"   Servers: {len(state['servers'])}")
    print(f"   Connections: {len(state['edges'])}")
    print("\n🚀 Now run the NEXUS MCP server - it will load this state instantly!")

asyncio.run(main())
