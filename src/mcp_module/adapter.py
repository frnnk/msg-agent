"""
Provides an adapter for connected MCP tools. Turns mcp tools into LangGraph ecosystem tools that can
be referenced and used by model nodes.
"""

import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
ASSISTANT_MCP = os.getenv('ASSISTANT_MCP_URL')

CLIENT = MultiServerMCPClient(
    {
        'assistant': {
            'transport': 'http',
            'url': ASSISTANT_MCP
        }
    }
)
TOOL_MAPPING = {
    'calendar': ["list_calendars", "list_events", "create_event", "update_event"],
}
HITL_TOOLS = {'create_event', 'update_event'}

_tools_cache = None
_cache_lock = asyncio.Lock()


async def get_tools(server_name: str = None, use_cache: bool = True):
    """Get tools from MCP server with optional caching.

    Only caches non-empty responses to avoid caching OAuth-needed states.
    """
    global _tools_cache

    if not use_cache:
        return await CLIENT.get_tools(server_name=server_name)

    async with _cache_lock:
        if _tools_cache is not None:
            return _tools_cache

        tools = await CLIENT.get_tools(server_name=server_name)
        if tools:
            _tools_cache = tools
        return tools


def invalidate_tools_cache():
    """Clear the tools cache. Call when tools may have changed."""
    global _tools_cache
    _tools_cache = None


if __name__ == '__main__':
    pass