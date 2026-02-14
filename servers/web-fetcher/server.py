from mcp.server.fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone

mcp = FastMCP("web-fetcher")


@mcp.tool()
def fetch_url(url: str) -> dict:
    """
    Fetches the textual content of a web page given its URL.
    Returns the extracted readable text, stripping HTML tags.
    Useful for web scraping, content extraction, news reading, and research.
    Supports any publicly accessible URL.

    Args:
        url: The full URL of the web page to fetch (e.g., https://example.com)

    Returns:
        A dictionary containing:
        - content: The extracted plain text from the page
        - fetched_at: ISO timestamp of when the fetch occurred
        - content_length: Character count of the extracted text
        - source_url: The URL that was fetched
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NexusBot/1.0)"
        }

        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=15.0)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Truncate very long content to prevent downstream failures
        MAX_CHARS = 50000
        if len(clean_text) > MAX_CHARS:
            clean_text = clean_text[:MAX_CHARS] + "\n\n[Content truncated]"

        return {
            "content": clean_text,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "content_length": len(clean_text),
            "source_url": url,
        }

    except Exception as e:
        return {
            "content": f"[Failed to fetch URL: {str(e)}]",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "content_length": 0,
            "source_url": url,
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")

