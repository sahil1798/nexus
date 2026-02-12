import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph
from nexus_core import database as db

async def main():
    print("=" * 60)
    print("NEXUS Persistence + Embeddings Test")
    print("=" * 60)

    # Phase 1: Register all servers
    print("\n📡 Phase 1: Registering servers...")
    registry = Registry()

    servers_to_register = [
        ('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py']),
        ('translator', 'uv', ['run', 'python', 'servers/translator/server.py']),
        ('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py']),
        ('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py']),
        ('sentiment-analyzer', 'uv', ['run', 'python', 'servers/sentiment-analyzer/server.py']),
    ]

    for name, cmd, args in servers_to_register:
        await registry.register(name, cmd, args)

    # Phase 2: Build graph with embeddings
    print("\n📊 Phase 2: Building capability graph...")
    graph = CapabilityGraph()
    graph.build_edges(registry.servers, incremental=True)

    # Phase 3: Show stats
    print("\n" + "=" * 60)
    print("📊 Database Statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Phase 4: Verify persistence
    print("\n🔄 Phase 4: Creating NEW instances to test persistence...")
    registry2 = Registry()
    graph2 = CapabilityGraph()

    print(f"   Servers loaded from DB: {len(registry2.servers)}")
    print(f"   Edges loaded from DB: {len(graph2.edges)}")

    for name, record in registry2.servers.items():
        summary = record.semantic_profile.plain_language_summary[:60] if record.semantic_profile else "N/A"
        print(f"   ✅ {name}: {summary}...")

    print("\n🎉 Persistence test PASSED!" if len(registry2.servers) == 5 else "\n❌ Persistence test FAILED")

asyncio.run(main())
