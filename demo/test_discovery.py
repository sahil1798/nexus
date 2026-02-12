import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph
from nexus_core.discovery import DiscoveryEngine

async def main():
    # Register servers
    registry = Registry()
    await registry.register('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py'])
    await registry.register('translator', 'uv', ['run', 'python', 'servers/translator/server.py'])
    await registry.register('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py'])
    await registry.register('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py'])

    # Build graph
    graph = CapabilityGraph()
    graph.build_edges(registry.servers)

    # Discover pipeline
    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(
        "Get the latest post from blog.example.com, translate it from French to English, summarize it, and post the summary in #team-updates on Slack."
    )
    pipeline.display()

asyncio.run(main())
