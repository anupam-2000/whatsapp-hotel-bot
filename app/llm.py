from openai import OpenAI
from app.config import OPENAI_API_KEY
import json

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Extract hotel booking details from the message.
Fields:
- name
- check_in
- check_out
- room_type

Return JSON. Use null if missing.
"""

def extract_info(message: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
    )

    try:
        return json.loads(response.output_text)
    except Exception:
        return {}
