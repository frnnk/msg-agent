"""
Main entrypoint for the agentic system.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from agentic.state import RequestState
from agentic.nodes.agent import policy_router, task_executor, response_formatter
from agentic.nodes.tool import use_tools
from agentic.nodes.human import human_confirmation, human_inquiry
from agentic.edges import route_from_task_executor, oauth_url_detection, route_from_human_confirmation


# each node in our agentic system is represented by a function
graph_config = StateGraph(state_schema=RequestState)
graph_config.add_node("policy_router", policy_router)
graph_config.add_node("task_executor", task_executor)
graph_config.add_node("response_formatter", response_formatter)
graph_config.add_node("use_tools", use_tools)
graph_config.add_node("human_confirmation", human_confirmation)

# conditional edges use a function to dynamically route
graph_config.add_edge(START, "policy_router")
graph_config.add_edge("policy_router", "task_executor")
graph_config.add_conditional_edges(
    "task_executor",
    route_from_task_executor,
    ["use_tools", "response_formatter", "human_confirmation"]
)
graph_config.add_conditional_edges(
    "use_tools",
    oauth_url_detection,
    ["task_executor", "response_formatter"]
)
graph_config.add_conditional_edges(
    "human_confirmation",
    route_from_human_confirmation,
    ["use_tools", "task_executor"]
)
graph_config.add_edge("response_formatter", END)

# set up a local memory checkpointer for now, volatile and not persistent
memory = InMemorySaver()
graph = graph_config.compile(checkpointer=memory)


async def run_graph(thread_id: str, initial_request: str) -> RequestState:
    message = await graph.ainvoke(
        input={
            "messages": [HumanMessage(initial_request)],
            "allowed_tool_types": []
        },
        config={
            "configurable": {"thread_id": thread_id}
        }
    )
    return message


if __name__ == "__main__":
    pass