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
from nexus_core.executor import PipelineExecutor

async def main():
    print("=" * 60)
    print("NEXUS - Full Pipeline Demo")
    print("=" * 60)

    # Phase 1: Register servers
    print("\n📡 PHASE 1: Registering MCP servers...")
    registry = Registry()
    await registry.register('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py'])
    await registry.register('translator', 'uv', ['run', 'python', 'servers/translator/server.py'])
    await registry.register('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py'])
    await registry.register('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py'])

    # Phase 2: Build capability graph
    print("\n📊 PHASE 2: Building capability graph...")
    graph = CapabilityGraph()
    graph.build_from_servers(registry.list_servers())

    # Phase 3: Discover pipeline
    print("\n🔍 PHASE 3: Discovering pipeline...")
    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(
        "Fetch content from https://example.com, summarize it, and post the summary to #team-updates on Slack."
    )
    pipeline.display()

    # Phase 4: Execute pipeline
    print("\n🚀 PHASE 4: Executing pipeline...")
    executor = PipelineExecutor(registry.servers)
    results = await executor.execute(
        pipeline,
        initial_input={"url": "https://example.com"},
        context={"channel": "#team-updates"}
    )

    # Show final result
    if results and results[-1].success:
        print("\n🎉 PIPELINE COMPLETE!")
        print(f"   Final output: {results[-1].output_data}")

asyncio.run(main())
