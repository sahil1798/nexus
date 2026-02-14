import asyncio
import json
import os
import sys
import time
sys.path.insert(0, '.')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nexus_core.models import ServerRecord, GraphEdge
from nexus_core.translator import TranslationEngine
from nexus_core.discovery import Pipeline, PipelineStep


class ExecutionResult:
    """Result of a single pipeline step."""
    def __init__(self, step: PipelineStep, input_data: dict, output_data: dict, duration: float, success: bool, error: str = None):
        self.step = step
        self.input_data = input_data
        self.output_data = output_data
        self.duration = duration
        self.success = success
        self.error = error


class PipelineExecutor:
    """Executes discovered pipelines by calling MCP servers."""

    def __init__(self, servers: dict[str, ServerRecord]):
        self.servers = servers
        self.translation_engine = TranslationEngine()

    async def execute(self, pipeline: Pipeline, initial_input: dict, context: dict) -> list[ExecutionResult]:
        """
        Execute a pipeline step by step. Never crashes — always returns results.
        """
        results = []
        current_data = initial_input
        all_outputs = {}  # Track ALL outputs for combining later

        print(f"\n{'='*60}")
        print("🚀 EXECUTING PIPELINE")
        print(f"{'='*60}")

        for i, step in enumerate(pipeline.steps):
            print(f"\n--- Step {i+1}/{len(pipeline.steps)}: {step.server_name}.{step.tool_name} ---")

            server = self.servers.get(step.server_name)
            if not server:
                error = f"Server '{step.server_name}' not found"
                print(f"   ❌ {error}")
                results.append(ExecutionResult(step, current_data, {}, 0, False, error))
                continue  # Don't break — try remaining steps

            # Prepare input (wrapped in try/except — never crash on translation)
            try:
                if step.edge:
                    print(f"   🔄 Translating from previous step...")
                    target_tool = next((t for t in server.tools if t.name == step.tool_name), None)
                    target_schema = target_tool.input_schema if target_tool else {}

                    # Special handling for slack-sender: combine all previous outputs
                    if step.server_name == "slack-sender":
                        step_input = self._build_slack_message(all_outputs, context)
                    else:
                        try:
                            spec = self.translation_engine.generate_spec(step.edge, current_data, target_schema)
                            step_input = self.translation_engine.apply_translation(spec, current_data, context)
                        except Exception as te:
                            print(f"   ⚠️ Translation failed ({te}), using direct mapping")
                            step_input = {}

                        # Fallback: fill missing required fields from source output
                        required = target_schema.get("required", [])
                        TEXT_ALIASES = ["content", "translated_text", "summary", "text", "result"]
                        for field in required:
                            if field not in step_input or not step_input[field]:
                                if field == "text":
                                    for alias in TEXT_ALIASES:
                                        if alias in current_data and current_data[alias]:
                                            step_input["text"] = current_data[alias]
                                            print(f"   ⚡ Fallback: mapped '{alias}' → 'text'")
                                            break
                                    # Last resort: dump all current data as text
                                    if "text" not in step_input or not step_input["text"]:
                                        step_input["text"] = json.dumps(current_data, default=str)[:5000]
                                        print(f"   ⚡ Fallback: used full current_data as text")
                                elif field == "url":
                                    # Try to get URL from context or current data
                                    if "url" in current_data:
                                        step_input["url"] = current_data["url"]
                                    elif "source_url" in current_data:
                                        step_input["url"] = current_data["source_url"]
                                    print(f"   ⚡ Fallback: mapped url from source")
                                elif field in current_data:
                                    step_input[field] = current_data[field]
                                    print(f"   ⚡ Fallback: mapped '{field}' directly")
                else:
                    step_input = dict(current_data)  # Copy to avoid mutation

                # Merge context fields needed by the tool
                for key, value in context.items():
                    if key not in step_input:
                        target_tool = next((t for t in server.tools if t.name == step.tool_name), None)
                        if target_tool and key in str(target_tool.input_schema):
                            step_input[key] = value

            except Exception as prep_err:
                print(f"   ⚠️ Input prep failed: {prep_err}")
                step_input = dict(current_data)

            print(f"   📥 Input: {json.dumps(step_input, indent=6, default=str)[:300]}...")

            # Execute the tool
            start_time = time.time()
            try:
                output = await self._call_tool(server, step.tool_name, step_input)
                duration = time.time() - start_time
                print(f"   📤 Output: {json.dumps(output, indent=6, default=str)[:300]}...")
                print(f"   ⏱️  Duration: {duration:.2f}s")

                results.append(ExecutionResult(step, step_input, output, duration, True))
                all_outputs[step.server_name] = output
                current_data = output

            except Exception as e:
                duration = time.time() - start_time
                error = str(e)
                print(f"   ❌ Error: {error}")
                results.append(ExecutionResult(step, step_input, {}, duration, False, error))
                # Don't break — continue with current_data so remaining steps can try

        self._print_summary(results)
        return results

    def _build_slack_message(self, all_outputs: dict, context: dict) -> dict:
        """Build a clean Slack message combining summary and sentiment."""
        message_parts = []

        # Add summary if available
        if "summarizer" in all_outputs:
            summary_data = all_outputs["summarizer"]
            if "summary" in summary_data:
                message_parts.append(f"📝 *Summary:*\n{summary_data['summary']}")
            if "key_points" in summary_data and summary_data["key_points"]:
                points = "\n".join([f"  • {p}" for p in summary_data["key_points"]])
                message_parts.append(f"\n🔑 *Key Points:*\n{points}")

        # Add sentiment if available
        if "sentiment-analyzer" in all_outputs:
            sentiment_data = all_outputs["sentiment-analyzer"]
            sentiment = sentiment_data.get("sentiment", "unknown")
            confidence = sentiment_data.get("confidence", 0)
            explanation = sentiment_data.get("explanation", "")

            # Emoji based on sentiment
            emoji = "😊" if sentiment == "positive" else "😐" if sentiment == "neutral" else "😟"

            message_parts.append(f"\n{emoji} *Sentiment:* {sentiment.title()} ({confidence:.0%} confidence)")
            if explanation:
                message_parts.append(f"_{explanation}_")

        # Combine into final message
        if message_parts:
            message_body = "\n".join(message_parts)
        else:
            # Fallback: use whatever data we have
            message_body = json.dumps(all_outputs, indent=2)[:500]

        return {
            "channel": context.get("channel", "#team-updates"),
            "message_body": message_body,
        }

    async def _call_tool(self, server: ServerRecord, tool_name: str, input_data: dict) -> dict:
        """Connect to an MCP server and call a specific tool."""
        server_params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env=dict(os.environ),  # Pass parent env vars (GEMINI_API_KEY, etc.)
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, input_data)

                if result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            try:
                                return json.loads(content.text)
                            except json.JSONDecodeError:
                                return {"result": content.text}
                return {}

    def _print_summary(self, results: list[ExecutionResult]):
        """Print execution summary."""
        print(f"\n{'='*60}")
        print("📊 EXECUTION SUMMARY")
        print(f"{'='*60}")

        total_time = sum(r.duration for r in results)
        success_count = sum(1 for r in results if r.success)

        for i, r in enumerate(results, 1):
            status = "✅" if r.success else "❌"
            print(f"   {status} Step {i}: {r.step.server_name}.{r.step.tool_name} ({r.duration:.2f}s)")
            if r.error:
                print(f"      Error: {r.error}")

        print(f"\n   Total steps: {len(results)}")
        print(f"   Successful: {success_count}/{len(results)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Status: {'SUCCESS ✅' if success_count == len(results) else 'FAILED ❌'}")
