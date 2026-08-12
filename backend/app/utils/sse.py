import json
from typing import Any, Dict

def format_sse_event(event_type: str, data: Any) -> str:
    """
    Formats a dictionary or string payload into standard SSE format:
    event: <event_type>
    data: <json_string>
    
    """
    payload = {
        "event": event_type,
        "data": data
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
