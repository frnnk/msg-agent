"""
Implementation of several agent nodes within the message assistant agentic system.
"""

import os
import logging
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from agentic.state import RequestState, NO_ACTION
from agentic.schema.prompts import POLICY_ROUTER, get_task_executor_prompt, RESPONSE_FORMATTER
from agentic.schema.models import PolicyRouterOut
from mcp_module.adapter import TOOL_MAPPING, CLIENT

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
    all_tools = await CLIENT.get_tools()
    allowed_tool_types = [TOOL_MAPPING[tool_type] for tool_type in state['allowed_tool_types']]
    allowed_tools = {tool for tool_type_list in allowed_tool_types for tool in tool_type_list}
    tools = [tool for tool in all_tools if tool.name in allowed_tools]
    tool_model = model.bind_tools(tools=tools)
    
    logging.info(f"Task allowed tools: {allowed_tools}")

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

    return {
        'messages': message
    }

async def response_formatter(state: RequestState):
    pending_action = state.get('pending_action', NO_ACTION)
    if pending_action['kind'] == 'oauth_url':
        return {
            'final_response': pending_action['message']
        }
    logging.debug(f"Current Messages: {state['messages']}")

    final_response = await model.ainvoke(
        [
            SystemMessage(content=RESPONSE_FORMATTER)
        ]
        + state['messages']
    )
    logging.info(f"Final response: {final_response.content}")

    return {
        'final_response': final_response.content
    }

if __name__ == '__main__':
    pass