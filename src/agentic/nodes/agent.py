"""
Implementation of several agent nodes within the message assistant agentic system.
"""

import os
import logging
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from agentic.state import RequestState
from agentic.schema.prompts import POLICY_ROUTER, TASK_EXECUTOR
from agentic.schema.models import PolicyRouterOut
from mcp_module.adapter import TOOL_MAPPING, TOOLS

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

model = init_chat_model(
    model='google_genai:gemini-2.5-flash-lite',
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
    logging.debug(f"Policy note: {schema['note']}")

    return {
        'allowed_tool_types': schema['allowed_tool_types']
    }

async def task_executor(state: RequestState):
    allowed_tool_types = [TOOL_MAPPING[tool_type] for tool_type in state['allowed_tool_types']]
    allowed_tools = {tool for tool_type_list in allowed_tool_types for tool in tool_type_list}
    tools = [tool for tool in TOOLS if tool.name in allowed_tools]
    tool_model = model.bind_tools(tools=tools)
    logging.debug(f"Task allowed tools: {allowed_tools}")

    message = await tool_model.ainvoke(
        [
            SystemMessage(
                content=TASK_EXECUTOR
            )
        ]
        + state['messages']
    )
    return {
        'messages': message
    }

async def response_formatter(state: RequestState):
    pass

if __name__ == '__main__':
    tool_model = model.bind_tools(tools=TOOLS)
    message = tool_model.invoke(
        [
            SystemMessage(
                content=TASK_EXECUTOR
            )
        ]
        + [HumanMessage("what events are on my calendar for the next week?")]
    )
    print(message)