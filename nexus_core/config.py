from google import genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.0-flash"

_last_call_time = 0


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini with rate limiting and retry."""
    global _last_call_time

    # Wait at least 4 seconds between calls (increased from 2)
    elapsed = time.time() - _last_call_time
    if elapsed < 4:
        time.sleep(4 - elapsed)

    max_retries = 5
    for attempt in range(max_retries):
        try:
            _last_call_time = time.time()
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 15 * (attempt + 1)  # 15, 30, 45, 60, 75 seconds
                print(f"   ⏳ Rate limited. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e

    raise Exception("Failed after max retries due to rate limiting")
