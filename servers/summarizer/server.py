from mcp.server.fastmcp import FastMCP
from google import genai
from dotenv import load_dotenv
import json
import os

load_dotenv()

mcp = FastMCP("summarizer")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@mcp.tool()
def summarize_text(text: str, max_sentences: int = 3) -> dict:
    """
    Condenses long text into a concise summary with key points.
    Useful for quickly understanding articles, documents, reports,
    blog posts, and any lengthy written content.

    Args:
        text: The long text to summarize
        max_sentences: Maximum number of sentences in the summary (default 3)

    Returns:
        A dictionary containing:
        - summary: A concise summary of the input text
        - key_points: A list of the most important points extracted from the text
        - original_length: Character count of the original text
        - summary_length: Character count of the summary
    """
    original_length = len(text)

    # Truncate very long text to avoid hitting token limits
    MAX_CHARS = 30000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[Text truncated for summarization]"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"""Summarize the following text in at most {max_sentences} sentences. 
Also extract 3-5 key points as a list.

Return your response as JSON in exactly this format, nothing else:
{{
    "summary": "your summary here",
    "key_points": ["point 1", "point 2", "point 3"]
}}

Text to summarize:
{text}""",
    )

    raw = response.text.strip()

    # Clean markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        summary = parsed.get("summary", raw)
        key_points = parsed.get("key_points", [])
    except json.JSONDecodeError:
        # Fallback: use the raw response as the summary
        summary = raw
        key_points = []

    return {
        "summary": summary,
        "key_points": key_points,
        "original_length": original_length,
        "summary_length": len(summary),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
