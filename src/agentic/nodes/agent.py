"""
Implementation of several agent nodes within the message assistant agentic system.
"""

import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

model = init_chat_model(
    model='google_genai:gemini-2.5-flash-lite',
    temperature=0
)

def classify_intent(state):
    pass

if __name__ == '__main__':
    response = model.invoke("what is chocolate made from")
    print(response)