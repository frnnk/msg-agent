"""
Implementation of several HITL nodes within the message assistant agentic system, handling
confirmations, form elicitations, and url oauth elicitations.
"""

from agentic.state import RequestState, NO_ACTION
from utils.helpers import get_last_ai_message
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import interrupt


async def human_confirmation(state: RequestState):
    """
    Human-in-the-loop confirmation node.

    Interrupts execution to get user approval for tool calls with side effects.
    Resume with /resume, and processes approval results, modifying state accordingly.

    Preserves memory by appending new messages instead of modifying existing ones.
    """
    tool_calls = state['pending_action']['tool_calls']

    # the interrupt() function pauses execution and returns when resumed
    # requires at least one argument (the value is not used, we use pending_action instead)
    approval_results = interrupt(None)

    # format of approval_results is found in (from /resume endpoint):
    approved_ids = [r['call_id'] for r in approval_results if r.get('approved')]
    rejected = [
        {
            'call_id': r['call_id'],
            'tool_name': next(tc['tool_name'] for tc in tool_calls if tc['call_id'] == r['call_id']),
            'feedback': r.get('feedback', 'Rejected without feedback')
        }
        for r in approval_results if not r.get('approved')
    ]

    last_ai_message = get_last_ai_message(state)

    # case 1: all approved, don't add any messages, just route to use_tools
    # the use_tools node will execute the tools and add ToolMessage responses
    # note: adding a HumanMessage here would break the message sequence since
    # AIMessage with tool_calls must be followed by ToolMessage, not HumanMessage
    if len(rejected) == 0:
        return {
            'pending_action': NO_ACTION,
            'approval_outcome': {
                'all_approved': True,
                'approved_call_ids': approved_ids,
                'rejected_feedback': []
            }
        }

    # case 2: all rejected, add ToolMessages for rejected calls, then route to task_executor
    # every tool_call called by AIMessage must have a corresponding ToolMessage response or things break
    if len(approved_ids) == 0:
        tool_messages = [
            ToolMessage(
                content=f"User rejected this action: {r['feedback']}",
                tool_call_id=r['call_id']
            )
            for r in rejected
        ]
        return {
            'messages': tool_messages,
            'pending_action': NO_ACTION,
            'approval_outcome': {
                'all_approved': False,
                'approved_call_ids': [],
                'rejected_feedback': rejected
            }
        }

    # case 3: partial approval
    # every tool_call in the original AIMessage needs a ToolMessage before any new AIMessage
    # so we add ToolMessages for all tool calls (approved and rejected), then add
    # a new AIMessage with only approved tool_calls for use_tools to execute
    approved_tool_messages = [
        ToolMessage(
            content="User approved this action. Proceeding with execution.",
            tool_call_id=call_id
        )
        for call_id in approved_ids
    ]
    rejected_tool_messages = [
        ToolMessage(
            content=f"User rejected this action: {r['feedback']}",
            tool_call_id=r['call_id']
        )
        for r in rejected
    ]

    approved_tool_calls = [
        tc for tc in last_ai_message.tool_calls
        if tc['id'] in approved_ids
    ]
    new_ai_message = AIMessage(
        content=last_ai_message.content,
        tool_calls=approved_tool_calls
    )

    return {
        'messages': approved_tool_messages + rejected_tool_messages + [new_ai_message],
        'pending_action': NO_ACTION,
        'approval_outcome': {
            'all_approved': False,
            'approved_call_ids': approved_ids,
            'rejected_feedback': rejected
        }
    }

async def human_inquiry(state: RequestState):
    pass