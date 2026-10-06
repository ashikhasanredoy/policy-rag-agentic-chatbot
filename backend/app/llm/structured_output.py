import json
import re
from typing import Dict, Any, Optional

def extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    """Robustly extracts JSON payload from LLM responses even if wrapped in markdown code blocks."""
    if not text:
        return None
    # Check for ```json ... ``` or ``` ... ```
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Direct match for outermost braces
    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass

    return None
