import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

TASK_EXECUTOR_MODEL = init_chat_model(
    model='openai:gpt-5-nano',
    temperature=0
)

POLICY_ROUTER_MODEL = init_chat_model(
    model='openai:gpt-4.1-nano',
    temperature=0
)
