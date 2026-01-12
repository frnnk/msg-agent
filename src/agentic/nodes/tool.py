"""
Implementation of tool nodes within the message assistant agentic system.
"""

from langgraph.prebuilt.tool_node import ToolNode
from agentic.state import RequestState
from mcp.adapter import TOOLS


TOOL_NODE = ToolNode(tools=TOOLS)

async def use_tools(state: RequestState):
    try:
        return await TOOL_NODE.ainvoke(state)
    except:
        # implement error handling later (elicitations, oauth, runtime)
        print("an error occured here")
        raise