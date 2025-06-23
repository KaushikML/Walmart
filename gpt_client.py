from __future__ import annotations

import json
import os
from typing import Any, List, Optional

import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

async def call_gpt(messages: List[dict], functions: Optional[List[dict]] = None) -> Any:
    """Call OpenAI ChatCompletion with optional function calling."""
    response = await openai.ChatCompletion.acreate(
        model="gpt-4o",
        messages=messages,
        functions=functions,
        function_call="auto" if functions else None,
    )
    msg = response.choices[0].message
    if msg.get("function_call"):
        return json.loads(msg["function_call"]["arguments"])
    return json.loads(msg.get("content", "{}"))
