import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langfuse.langchain import CallbackHandler

load_dotenv()

# placeholder keys so the package imports without a .env; real keys from the
# environment or .env take precedence because setdefault never overwrites
# TODO(template): provide real provider keys via .env (see .env.example)
os.environ.setdefault('OPENAI_API_KEY', 'sk-PLACEHOLDER')
os.environ.setdefault('GOOGLE_API_KEY', 'PLACEHOLDER')

# model identifiers, overridable via env (format "provider:model")
# TODO(template): point these at your provider and model
TASK_EXECUTOR_MODEL = init_chat_model(
    model=os.getenv('TASK_EXECUTOR_MODEL', 'openai:gpt-5-nano'),
    temperature=0
)

POLICY_ROUTER_MODEL = init_chat_model(
    model=os.getenv('POLICY_ROUTER_MODEL', 'openai:gpt-5-nano'),
    temperature=0
)

# optional Langfuse observability, only enabled when both keys are set
# TODO(template): set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable tracing
LANGFUSE_CALLBACK = None
if os.getenv('LANGFUSE_PUBLIC_KEY') and os.getenv('LANGFUSE_SECRET_KEY'):
    LANGFUSE_CALLBACK = CallbackHandler()
