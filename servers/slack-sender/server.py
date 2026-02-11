from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os

load_dotenv()

mcp = FastMCP("slack-sender")
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))


@mcp.tool()
def send_slack_message(channel: str, message_body: str) -> dict:
    """
    Sends a message to a specified Slack channel.
    Useful for notifications, alerts, team communication,
    automated reporting, and delivering content to team members.
    The bot must be invited to the target channel before sending.

    Args:
        channel: The Slack channel to post to (e.g., "#team-updates" or "team-updates")
        message_body: The message text to send. Supports Slack markdown formatting.

    Returns:
        A dictionary containing:
        - success: Whether the message was sent successfully
        - channel: The channel the message was posted to
        - timestamp: The Slack message timestamp (unique message ID)
        - message_preview: First 100 characters of the sent message
    """
    # Ensure channel starts with #
    if not channel.startswith("#"):
        channel = f"#{channel}"

    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=message_body,
        )

        return {
            "success": True,
            "channel": channel,
            "timestamp": response["ts"],
            "message_preview": message_body[:100],
        }

    except SlackApiError as e:
        return {
            "success": False,
            "channel": channel,
            "error": str(e.response["error"]),
            "message_preview": message_body[:100],
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
