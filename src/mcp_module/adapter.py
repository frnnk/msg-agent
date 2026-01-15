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


async def get_tools_by_server(server_name: str = None):
    tools = await CLIENT.get_tools(server_name=server_name)
    return tools


if __name__ == '__main__':
    asyncio.run(get_tools_by_server())