"""
Provides prompts for agent nodes.
"""

import json
from mcp_module.adapter import TOOLS
from pydantic import BaseModel, Field
from typing import List

def tool_catalog(tools):
    return [
        {
            "name": t.name,
            "description": (t.description or "").strip()[:400],
        }
        for t in tools
    ]

POLICY_ROUTER = f"""You are PolicyRouter. Decide which tools are permitted for this request.

Tools:
{json.dumps(tool_catalog(TOOLS), ensure_ascii=False)}

Rules:
- Only include tools from the provided tool catalog that can complete the request.
- Prefer the smallest set of tools needed.
- If no tools are allowed, set decision="refuse" and explain briefly in note; allowed_tools must be [].
- Otherwise if tools are allowed, set decision="allow" and briefly explain rationale in note; allowed_tools must be a list of tool name strings.
- No markdown, no extra keys, no text outside JSON.
"""

class PolicyRouterOut(BaseModel):
    decision: str
    note: str
    allowed_tools: List[str]

if __name__ == "__main__":
    pass