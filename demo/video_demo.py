#!/usr/bin/env python3
"""
NEXUS Video Demo Script
-----------------------
A clean, visually appealing demo for recording.
Run with: uv run python demo/video_demo.py
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.registry import Registry
from nexus_core.graph import CapabilityGraph
from nexus_core.discovery import DiscoveryEngine
from nexus_core.executor import PipelineExecutor


# ANSI colors for beautiful output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(text):
    width = 70
    print(f"\n{Colors.CYAN}{'═' * width}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.CYAN}{'═' * width}{Colors.END}\n")


def print_step(num, text):
    print(f"{Colors.YELLOW}  [{num}]{Colors.END} {text}")


def print_success(text):
    print(f"{Colors.GREEN}  ✓ {text}{Colors.END}")


def print_info(text):
    print(f"{Colors.DIM}    {text}{Colors.END}")


def pause(msg="Press Enter to continue..."):
    input(f"\n{Colors.DIM}  {msg}{Colors.END}")


def type_effect(text, delay=0.03):
    """Simulate typing effect for dramatic moments."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


async def main():
    clear_screen()

    # Title screen
    print(f"""
{Colors.CYAN}{Colors.BOLD}
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
{Colors.END}
{Colors.DIM}    The Intelligent MCP Broker{Colors.END}

{Colors.YELLOW}    "MCP servers are powerful alone.{Colors.END}
{Colors.YELLOW}     NEXUS makes them powerful together."{Colors.END}
    """)

    pause("Press Enter to begin the demo...")
    clear_screen()

    # Initialize
    registry = Registry()
    graph = CapabilityGraph()

    # ========== PART 1: REGISTRATION ==========
    print_header("PART 1: Registering MCP Servers")

    print(f"  {Colors.DIM}NEXUS connects to MCP servers, reads their metadata,{Colors.END}")
    print(f"  {Colors.DIM}and uses AI to understand their capabilities.{Colors.END}\n")

    servers = [
        ('web-fetcher', 'Fetches content from web pages'),
        ('summarizer', 'Summarizes long text'),
        ('slack-sender', 'Posts messages to Slack'),
    ]

    for name, desc in servers:
        print(f"\n  {Colors.BLUE}📡 Registering '{name}'...{Colors.END}")
        await registry.register(name, 'uv', ['run', 'python', f'servers/{name}/server.py'])
        print_success(f"{name} registered")
        print_info(desc)

    pause()
    clear_screen()

    # ========== PART 2: CAPABILITY GRAPH ==========
    print_header("PART 2: Building Capability Graph")

    print(f"  {Colors.DIM}NEXUS analyzes how servers can connect together.{Colors.END}")
    print(f"  {Colors.DIM}AI evaluates each pair for compatibility.{Colors.END}\n")

    graph.build_from_servers(registry.list_servers())

    print(f"\n  {Colors.GREEN}📊 Graph complete: {len(graph.edges)} connections discovered{Colors.END}")

    pause()
    clear_screen()

    # ========== PART 3: PIPELINE DISCOVERY ==========
    print_header("PART 3: Natural Language → Pipeline")

    request = "Fetch example.com, summarize it, and post to #team-updates on Slack"

    print(f"  {Colors.BOLD}User Request:{Colors.END}")
    print(f"  {Colors.YELLOW}\"{request}\"{Colors.END}\n")

    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(request)

    print(f"\n  {Colors.GREEN}🛤️  Pipeline Discovered (confidence: {pipeline.confidence:.0%}){Colors.END}")
    for i, step in enumerate(pipeline.steps, 1):
        conn = step.edge.compatibility_type if step.edge else "entry"
        print(f"      Step {i}: {step.server_name}.{step.tool_name} ({conn})")

    pause()
    clear_screen()

    # ========== PART 4: EXECUTION ==========
    print_header("PART 4: Executing Pipeline")

    print(f"  {Colors.DIM}NEXUS calls each server, translating data between steps.{Colors.END}\n")

    executor = PipelineExecutor(registry.servers)
    results = await executor.execute(
        pipeline,
        initial_input={"url": "https://example.com"},
        context={"channel": "#team-updates"}
    )

    pause()
    clear_screen()

    # ========== PART 5: LIVE ADAPTATION ==========
    print_header("PART 5: Live Adaptation — Adding New Server")

    print(f"  {Colors.BOLD}Watch NEXUS adapt when a new server appears...{Colors.END}\n")

    pause("Press Enter to add Sentiment Analyzer...")

    print(f"\n  {Colors.BLUE}📡 Registering 'sentiment-analyzer'...{Colors.END}")
    await registry.register('sentiment-analyzer', 'uv', ['run', 'python', 'servers/sentiment-analyzer/server.py'])
    print_success("sentiment-analyzer registered")

    print(f"\n  {Colors.BLUE}📊 Rebuilding capability graph...{Colors.END}")
    graph = CapabilityGraph()
    graph.build_from_servers(registry.list_servers())
    print_success(f"Graph updated: {len(graph.edges)} connections")

    pause()
    clear_screen()

    # ========== PART 6: ENHANCED PIPELINE ==========
    print_header("PART 6: Enhanced Pipeline with Sentiment")

    request2 = "Fetch example.com, summarize it, analyze sentiment, post to Slack"

    print(f"  {Colors.BOLD}New Request:{Colors.END}")
    print(f"  {Colors.YELLOW}\"{request2}\"{Colors.END}\n")

    engine = DiscoveryEngine(registry.servers, graph.edges)
    pipeline = engine.discover(request2)

    print(f"\n  {Colors.GREEN}🛤️  Enhanced Pipeline (confidence: {pipeline.confidence:.0%}){Colors.END}")
    for i, step in enumerate(pipeline.steps, 1):
        conn = step.edge.compatibility_type if step.edge else "entry"
        print(f"      Step {i}: {step.server_name}.{step.tool_name} ({conn})")

    pause("Press Enter to execute enhanced pipeline...")

    executor = PipelineExecutor(registry.servers)
    results = await executor.execute(
        pipeline,
        initial_input={"url": "https://example.com"},
        context={"channel": "#team-updates"}
    )

    # ========== FINALE ==========
    clear_screen()
    print(f"""
{Colors.GREEN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                    🎉 DEMO COMPLETE! 🎉                       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
{Colors.END}

  {Colors.CYAN}What you just witnessed:{Colors.END}

    {Colors.GREEN}✓{Colors.END} NEXUS registered MCP servers and profiled their capabilities
    {Colors.GREEN}✓{Colors.END} AI discovered how servers can chain together
    {Colors.GREEN}✓{Colors.END} Natural language request → executable pipeline
    {Colors.GREEN}✓{Colors.END} Automatic data translation between incompatible schemas
    {Colors.GREEN}✓{Colors.END} Live adaptation when a new server was added
    {Colors.GREEN}✓{Colors.END} Enhanced pipeline with the new capability

  {Colors.YELLOW}Check your #team-updates Slack channel for the formatted message!{Colors.END}

  {Colors.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}

  {Colors.CYAN}NEXUS: Making MCP servers work together, intelligently.{Colors.END}

    """)


if __name__ == "__main__":
    asyncio.run(main())
