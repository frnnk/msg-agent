"""
Implementation of tool nodes within the message assistant agentic system.
"""

import logging
from langgraph.prebuilt.tool_node import ToolNode
from agentic.state import RequestState
from mcp_module.adapter import TOOLS
from mcp.shared.exceptions import McpError
from langchain.messages import ToolMessage


TOOL_NODE = ToolNode(tools=TOOLS)
URL_ELICITATION_ERROR = -32042

async def use_tools(state: RequestState):
    try:
        return await TOOL_NODE.ainvoke(state)
    except McpError as e:
        logging.error(f"an mcp error occured here: {e}")
        error = e.error
        data = error.data

        if error.code == URL_ELICITATION_ERROR:
            elicitation = data['elicitations'][0]
            return {
                'is_oauth': True,
                'pending_action': {
                    'kind': 'mcp_elicitation',
                    'mode': 'url',
                    'elicitation_id': elicitation['elicitationId'],
                    'url': elicitation['url'],
                    'message': elicitation['message']
                }
            }
        
        raise
    except Exception as e:
        logging.error(f"an error occured here: {e}")
        raise