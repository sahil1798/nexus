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

    parsed = json.loads(raw)

    return {
        "sentiment": parsed["sentiment"],
        "confidence": parsed["confidence"],
        "tone_words": parsed["tone_words"],
        "explanation": parsed["explanation"],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
