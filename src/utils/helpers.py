"""
Docstring for utils.helpers
"""

def tool_catalog(tools):
    return [
        {
            "name": t.name,
            "description": (t.description or "").strip()[:400],
        }
        for t in tools
    ]