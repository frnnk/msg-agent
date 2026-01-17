"""
Implementation of several agent nodes within the message assistant agentic system.
"""

import os
import logging
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from agentic.state import RequestState, NO_ACTION
from agentic.schema.prompts import POLICY_ROUTER, get_task_executor_prompt
from agentic.schema.models import PolicyRouterOut
from agentic.schema.tools import request_clarification, CLARIFICATION_TOOL_NAME
from mcp_module.adapter import TOOL_MAPPING, HITL_TOOLS, CLIENT

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

GEMINI_MODEL = 'google_genai:gemini-2.5-flash-lite'
GPT_MODEL = 'openai:gpt-5-nano'

model = init_chat_model(
    model=GPT_MODEL,
    temperature=0
)

async def policy_router(state: RequestState):
    """
    Policy router node.

    Analyzes the user request to determine which tool types (calendar) are
    permitted for the current conversation. Adds allowed_tool_types to state.

    Uses structured output to ensure consistent policy decisions.
    """
    structured_model = model.with_structured_output(PolicyRouterOut)
    message = await structured_model.ainvoke(
        [
            SystemMessage(
                content=POLICY_ROUTER
            )
        ]
        + state['messages']
    )
    schema = message.model_dump()
    logging.info(f"Policy note: {schema['note']}")

    return {
        'allowed_tool_types': schema['allowed_tool_types']
    }

async def task_executor(state: RequestState):
    """
    Task executor node.

    Main agent that processes user requests by invoking appropriate MCP tools.
    Loads tools based on allowed_tool_types from policy_router.

    Detects HITL tools and sets pending_action for human confirmation when needed.
    """
    all_tools = await CLIENT.get_tools()
    allowed_tool_types = [TOOL_MAPPING[tool_type] for tool_type in state['allowed_tool_types']]
    allowed_tools = {tool for tool_type_list in allowed_tool_types for tool in tool_type_list}
    mcp_tools = [tool for tool in all_tools if tool.name in allowed_tools]
    tools = mcp_tools + [request_clarification]

    logging.info(f"Task allowed tools: {allowed_tools}")

    tool_model = model.bind_tools(tools=tools)
    message = await tool_model.ainvoke(
        [
            SystemMessage(
                content=get_task_executor_prompt()
            )
        ]
        + state['messages']
    )
    logging.info(f"Task Executor Message: {message.content}")
    logging.info(f"Task Executor Tools Called: {message.tool_calls}")

    # check for clarification requests first (takes priority)
    clarification_calls = [tc for tc in message.tool_calls if tc['name'] == CLARIFICATION_TOOL_NAME]
    if clarification_calls:
        return {
            'messages': message,
            'pending_action': {
                'kind': 'clarification',
                'clarifications': [
                    {
                        'call_id': tc['id'],
                        'question': tc['args'].get('question', ''),
                        'context': tc['args'].get('context', '')
                    }
                    for tc in clarification_calls
                ]
            }
        }

    # check for any tool usage that needs human confirmation
    # extract full tool call info (id, name, args) for HITL tools
    hitl_tool_calls = [
        {
            'call_id': tc['id'],
            'tool_name': tc['name'],
            'arguments': tc['args']
        }
        for tc in message.tool_calls
        if tc['name'] in HITL_TOOLS
    ]
    if hitl_tool_calls:
        return {
            'messages': message,
            'pending_action': {
                'kind': 'confirmation',
                'tool_calls': hitl_tool_calls
            }
        }

    if not message.tool_calls:
        return {
            'messages': message,
            'final_response': message.content
        }

    return {
        'messages': message
    }

if __name__ == '__main__':
    pass