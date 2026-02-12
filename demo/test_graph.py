import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph

async def main():
    # First register all servers
    registry = Registry()
    await registry.register('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py'])
    await registry.register('translator', 'uv', ['run', 'python', 'servers/translator/server.py'])
    await registry.register('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py'])
    await registry.register('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py'])

    # Build the capability graph
    graph = CapabilityGraph()
    graph.build_from_servers(registry.list_servers())

    # Show paths from web-fetcher to slack-sender
    print("\n🛤️  Paths from web-fetcher to slack-sender:")
    paths = graph.find_paths('web-fetcher', 'slack-sender')
    for i, path in enumerate(paths, 1):
        route = " → ".join([f"{e.source_server}" for e in path] + [path[-1].target_server])
        print(f"   Path {i}: {route}")

asyncio.run(main())
