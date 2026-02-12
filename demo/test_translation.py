import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nexus_core.translator import TranslationEngine
from nexus_core.models import GraphEdge

engine = TranslationEngine()

# Simulate: summarizer output -> slack-sender input
edge = GraphEdge(
    source_server="summarizer",
    source_tool="summarize_text",
    target_server="slack-sender",
    target_tool="send_slack_message",
    compatibility_type="translatable",
    confidence=0.85,
    translation_hint="The 'summary' field from the summarizer output can be used as the 'message_body' for the slack-sender. The user must still specify the slack 'channel'.",
)

source_output = {
    "summary": "AI is transforming healthcare, finance, and education with applications in diagnostics, fraud detection, and adaptive learning.",
    "key_points": [
        "AI diagnostics in healthcare",
        "Fraud detection in finance",
        "Adaptive learning in education",
    ],
    "original_length": 605,
    "summary_length": 130,
}

target_input_schema = {
    "type": "object",
    "properties": {
        "channel": {"type": "string"},
        "message_body": {"type": "string"},
    },
    "required": ["channel", "message_body"],
}

context = {
    "channel": "#team-updates",
}

print("📝 Generating translation spec...")
spec = engine.generate_spec(edge, source_output, target_input_schema)
print(json.dumps(spec, indent=2))

print("\n🔄 Applying translation...")
result = engine.apply_translation(spec, source_output, context)
print(json.dumps(result, indent=2))
