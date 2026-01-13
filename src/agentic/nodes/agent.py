"""
Implementation of several agent nodes within the message assistant agentic system.
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from agentic.state import RequestState
from agentic.schema.prompts import POLICY_ROUTER
from agentic.schema.models import PolicyRouterOut

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

    return {
        'allowed_tool_types': schema['allowed_tool_types']
    }

async def task_executor(state: RequestState):
    pass

async def response_formatter(state: RequestState):
    pass

if __name__ == '__main__':
    structured_model = model.with_structured_output(PolicyRouterOut)
    message = structured_model.invoke(
        [
            SystemMessage(
                content=POLICY_ROUTER
            )
        ]
        + [HumanMessage("Create a reservation for next Tuesday")]
    )
    print(message.model_dump())