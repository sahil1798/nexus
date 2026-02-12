import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.registry import Registry

async def main():
    registry = Registry()

    await registry.register('web-fetcher', 'uv', ['run', 'python', 'servers/web-fetcher/server.py'])
    await registry.register('translator', 'uv', ['run', 'python', 'servers/translator/server.py'])
    await registry.register('summarizer', 'uv', ['run', 'python', 'servers/summarizer/server.py'])
    await registry.register('slack-sender', 'uv', ['run', 'python', 'servers/slack-sender/server.py'])

    print("\n" + "=" * 60)
    print(f"Total servers registered: {len(registry.list_servers())}")
    for s in registry.list_servers():
        summary = s.semantic_profile.plain_language_summary[:80]
        print(f"  - {s.name} [{s.status}]: {summary}...")

asyncio.run(main())
