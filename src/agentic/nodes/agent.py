"""
Implementation of several agent nodes within the message assistant agentic system.
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agentic.state import RequestState
from mcp.adapter import TOOLS

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

model = init_chat_model(
    model='google_genai:gemini-2.5-flash-lite',
    temperature=0
)

async def policy_router(state: RequestState):
    pass

async def task_executor(state: RequestState):
    pass

async def response_formatter(state: RequestState):
    pass

if __name__ == '__main__':
    response = model.invoke("what is chocolate made from")
    print(response)