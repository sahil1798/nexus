from mcp.server.fastmcp import FastMCP
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

mcp = FastMCP("translator")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@mcp.tool()
def translate_text(text: str, source_language: str, target_language: str) -> dict:
    """
    Translates text from one language to another.
    Useful for internationalization, cross-language communication,
    localization, and making content accessible to speakers of different languages.
    Supports all major world languages.

    Args:
        text: The text to translate
        source_language: The language the text is currently in (e.g., "French", "en", "Spanish")
        target_language: The language to translate the text into (e.g., "English", "ja", "German")

    Returns:
        A dictionary containing:
        - translated_text: The translated version of the input text
        - source_language: The source language that was specified
        - target_language: The target language that was specified
        - original_length: Character count of the original text
        - translated_length: Character count of the translated text
    """
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"You are a professional translator. Translate the following text from {source_language} to {target_language}. Return ONLY the translated text, nothing else. Preserve the original formatting and tone.\n\nText to translate:\n{text}",
    )

    translated = response.text.strip()

    return {
        "translated_text": translated,
        "source_language": source_language,
        "target_language": target_language,
        "original_length": len(text),
        "translated_length": len(translated),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
