"""
Implementation of tool nodes within the message assistant agentic system.
"""

import logging
from langgraph.prebuilt.tool_node import ToolNode
from langchain_core.messages import ToolMessage
from agentic.state import RequestState
from mcp_module.adapter import CLIENT
from mcp.shared.exceptions import McpError
from utils.helpers import get_last_ai_message


URL_ELICITATION_ERROR = -32042

async def use_tools(state: RequestState):
    """
    Tool execution node.

    Executes MCP tool calls from the task_executor using LangGraph's ToolNode.
    Handles OAuth URL elicitation errors by capturing the auth URL in pending_action.

    Returns ToolMessage results to state for the task_executor to process.
    """
    try:
        tools = await CLIENT.get_tools()
        tool_node = ToolNode(tools)
        return await tool_node.ainvoke(state)
    except McpError as e:
        logging.error(f"an mcp error occured here: {e}")
        error = e.error
        data = error.data

        if error.code == URL_ELICITATION_ERROR:
            elicitation = data['elicitations'][0]
            last_ai_message = get_last_ai_message(state)
            tool_messages = [
                ToolMessage(
                    content="Authentication required. Please complete OAuth flow.",
                    tool_call_id=tc['id']
                )
                for tc in last_ai_message.tool_calls
            ]
            return {
                'messages': tool_messages,
                'pending_action': {
                    'kind': 'oauth_url',
                    'elicitation_id': elicitation['elicitationId'],
                    'url': elicitation['url'],
                    'message': elicitation['message']
                }
            }

        raise
    except Exception as e:
        logging.error(f"an error occured here: {e}")
        raise