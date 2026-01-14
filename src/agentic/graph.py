"""
Main entrypoint for the agentic system.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage
from agentic.state import RequestState
from agentic.nodes.agent import policy_router, task_executor, response_formatter
from agentic.nodes.tool import use_tools
from agentic.nodes.human import human_confirmation, human_inquiry
from agentic.edges import continue_to_tool, oauth_url_detection


graph_config = StateGraph(state_schema=RequestState)
graph_config.add_node("policy_router", policy_router)
graph_config.add_node("task_executor", task_executor)
graph_config.add_node("response_formatter", response_formatter)
graph_config.add_node("use_tools", use_tools)
graph_config.add_node("human_inquiry", human_inquiry)

graph_config.add_edge(START, "policy_router")
graph_config.add_edge("policy_router", "task_executor")
graph_config.add_conditional_edges(
    "task_executor",
    continue_to_tool,
    ["use_tools", "response_formatter"]
)
graph_config.add_conditional_edges(
    "use_tools",
    oauth_url_detection,
    ["task_executor", "response_formatter"]
)
graph_config.add_edge("response_formatter", END)

graph = graph_config.compile()

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    message = asyncio.run(graph.ainvoke({
        "messages": [HumanMessage("Show me the events on my primary calendar for the next 7 days.")],
        "allowed_tool_types": []
    }))
    
    print()
    print(message['final_response'])
    if message.get('is_oauth'):
        print()
        print(message['pending_action']['url'])