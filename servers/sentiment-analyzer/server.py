from mcp.server.fastmcp import FastMCP
from google import genai
from dotenv import load_dotenv
import json
import os

load_dotenv()

mcp = FastMCP("sentiment-analyzer")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@mcp.tool()
def analyze_sentiment(text: str) -> dict:
    """
    Analyzes the sentiment and emotional tone of a given text.
    Useful for understanding the mood of articles, reviews, social media posts,
    customer feedback, blog posts, and any written content.
    Detects whether content is positive, negative, or neutral and identifies
    specific emotional tones.

    Args:
        text: The text to analyze for sentiment and tone

    Returns:
        A dictionary containing:
        - sentiment: The overall sentiment (positive, negative, neutral, mixed)
        - confidence: Confidence score from 0.0 to 1.0
        - tone_words: List of words describing the emotional tone
        - explanation: Brief explanation of why this sentiment was detected
    """
    # Truncate very long text to avoid hitting token limits
    MAX_CHARS = 30000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[Text truncated for analysis]"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"""Analyze the sentiment and emotional tone of the following text.

Return your response as JSON in exactly this format, nothing else:
{{
    "sentiment": "positive or negative or neutral or mixed",
    "confidence": 0.85,
    "tone_words": ["word1", "word2", "word3"],
    "explanation": "brief explanation here"
}}

Text to analyze:
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
        return {
            "sentiment": parsed.get("sentiment", "neutral"),
            "confidence": parsed.get("confidence", 0.5),
            "tone_words": parsed.get("tone_words", []),
            "explanation": parsed.get("explanation", raw),
        }
    except json.JSONDecodeError:
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "tone_words": [],
            "explanation": raw,
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
