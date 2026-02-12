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
    print("=" * 70)
    print("  NEXUS - The Intelligent MCP Broker")
    print("  'MCP servers are powerful alone. NEXUS makes them powerful together.'")
    print("=" * 70)

    registry = Registry()
    graph = CapabilityGraph()

    # DEMO PART 1: Register initial 4 servers
    print("\n" + "=" * 70)
    print("DEMO PART 1: Registering MCP Servers")
    print("=" * 70)

    await registry.register('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py'])
    await registry.register('translator', 'uv', ['run', 'python', 'servers/translator/server.py'])
    await registry.register('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py'])
    await registry.register('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py'])

    # Build initial graph
    print("\n📊 Building capability graph...")
    graph.build_from_servers(registry.list_servers())

    # DEMO PART 2: Execute first pipeline (with translation)
    print("\n" + "=" * 70)
    print("DEMO PART 2: First Pipeline Execution")
    print("=" * 70)

    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(
        "Fetch content from https://example.com, translate it from English to Spanish, summarize it, and post to #team-updates on Slack."
    )
    pipeline.display()

    executor = PipelineExecutor(registry.servers)
    await executor.execute(
        pipeline,
        initial_input={"url": "https://example.com"},
        context={
            "channel": "#team-updates",
            "source_language": "English",
            "target_language": "Spanish"
        }
    )

    # DEMO PART 3: Add sentiment analyzer live
    print("\n" + "=" * 70)
    print("DEMO PART 3: Adding New Server LIVE")
    print("=" * 70)
    input("\n>>> Press Enter to add the Sentiment Analyzer server...")

    await registry.register('sentiment-analyzer', 'uv', ['run', 'python', 'servers/sentiment-analyzer/server.py'])

    # Rebuild graph with new server
    print("\n📊 Rebuilding capability graph with new server...")
    graph = CapabilityGraph()
    graph.build_from_servers(registry.list_servers())

    # DEMO PART 4: Enhanced pipeline with sentiment
    print("\n" + "=" * 70)
    print("DEMO PART 4: Enhanced Pipeline with Sentiment Analysis")
    print("=" * 70)

    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(
        "Fetch content from https://example.com, summarize it, analyze its sentiment, and post a message to #team-updates on Slack that includes both the summary and the sentiment."
    )
    pipeline.display()

    await executor.execute(
        pipeline,
        initial_input={"url": "https://example.com"},
        context={"channel": "#team-updates"}
    )

    print("\n" + "=" * 70)
    print("🎉 DEMO COMPLETE!")
    print("=" * 70)
    print("\nWhat you just witnessed:")
    print("  1. NEXUS registered 4 MCP servers and understood their capabilities")
    print("  2. NEXUS built a capability graph with AI-discovered connections")
    print("  3. NEXUS discovered a pipeline from natural language")
    print("  4. NEXUS executed the pipeline with automatic data translation")
    print("  5. A 5th server was added LIVE - NEXUS adapted automatically!")
    print("  6. NEXUS discovered an enhanced pipeline using the new server")
    print("\nCheck your #team-updates Slack channel for the messages!")

asyncio.run(main())
