"""
Implementation of tool nodes within the message assistant agentic system.
"""

from langgraph.prebuilt.tool_node import ToolNode
from agentic.state import RequestState
from mcp_module.adapter import TOOLS
from mcp.shared.exceptions import McpError


TOOL_NODE = ToolNode(tools=TOOLS)

async def use_tools(state: RequestState):
    try:
        return await TOOL_NODE.ainvoke(state)
    except McpError as e:
        print(f"an mcp error occured here: {e}")
    except Exception as e:
        # implement error handling later (elicitations, oauth, runtime)
        print(f"an error occured here: {e}")
        raise