"""
Main entrypoint for the agentic system.
"""

from langgraph.graph import StateGraph, START, END
from agentic.state import RequestState
from agentic.nodes.agent import policy_router, task_executor
from agentic.nodes.tool import use_tools
from agentic.nodes.human import human_confirmation, human_inquiry
from langchain.messages import HumanMessage
from typing import Literal

def should_continue(state: RequestState) -> Literal["use_tools", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "use_tools"

    return END

graph_config = StateGraph(state_schema=RequestState)
graph_config.add_node("policy_router", policy_router)
graph_config.add_node("task_executor", task_executor)
graph_config.add_node("use_tools", use_tools)
graph_config.add_node("human_inquiry", human_inquiry)

graph_config.add_edge(START, "policy_router")
graph_config.add_edge("policy_router", "task_executor")
graph_config.add_conditional_edges(
    "task_executor",
    should_continue,
    ["use_tools", END]
)
graph_config.add_edge("use_tools", "task_executor")

graph = graph_config.compile()

if __name__ == "__main__":
    import asyncio
    message = asyncio.run(graph.ainvoke({
        "messages": [HumanMessage("Can you show me the events on my primary calendar for the next week")],
        "pending_action": None,
        "allowed_tool_types": []
    }))
    print(message)