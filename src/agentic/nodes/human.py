"""
Implementation of several HITL nodes within the message assistant agentic system, handling
confirmations, form elicitations, and url oauth elicitations.
"""

from typing import Callable
from agentic.state import RequestState, NO_ACTION
from utils.helpers import get_last_ai_message
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import interrupt
from mcp_module.adapter import HITL_TOOLS


def create_tool_messages(call_ids: list[str], content: str | Callable[[str], str]) -> list[ToolMessage]:
    """Create ToolMessages for given call IDs with specified content."""
    if callable(content):
        return [ToolMessage(content=content(cid), tool_call_id=cid) for cid in call_ids]
    return [ToolMessage(content=content, tool_call_id=cid) for cid in call_ids]


def build_confirmation_result(
    messages: list | None,
    all_approved: bool,
    approved_call_ids: list[str],
    rejected_feedback: list
) -> dict:
    """Build the return dict for human_confirmation node."""
    result = {
        'pending_action': NO_ACTION,
        'approval_outcome': {
            'all_approved': all_approved,
            'approved_call_ids': approved_call_ids,
            'rejected_feedback': rejected_feedback
        }
    }
    if messages:
        result['messages'] = messages
    return result


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

    # get non-HITL tools that are auto-approved
    hitl_call_ids = {tc['call_id'] for tc in tool_calls}
    non_hitl_tool_calls = [tc for tc in last_ai_message.tool_calls if tc['id'] not in hitl_call_ids]
    non_hitl_call_ids = [tc['id'] for tc in non_hitl_tool_calls]

    # create filler ToolMessages (in preparation for creating a new filtered AIMessage)
    rejected_feedback_map = {r['call_id']: r['feedback'] for r in rejected}
    approved_tool_msgs = create_tool_messages(
        approved_ids,
        "User approved this action. Proceeding with execution."
    )
    rejected_tool_msgs = create_tool_messages(
        [r['call_id'] for r in rejected],
        lambda cid: f"User rejected this action: {rejected_feedback_map[cid]}"
    )
    non_hitl_tool_msgs = create_tool_messages(
        non_hitl_call_ids,
        "Auto-approved (non-confirmation tool). Proceeding with execution."
    )

    # case 1: all approved, don't add any messages, just route to use_tools
    # the use_tools node will execute the tools and add ToolMessage responses
    if len(rejected) == 0:
        return build_confirmation_result(None, True, approved_ids, [])

    # case 2: all HITL rejected
    # every tool_call in AIMessage must have a corresponding filler ToolMessage
    if len(approved_ids) == 0:
        all_tool_messages = rejected_tool_msgs + non_hitl_tool_msgs

        # if non-HITL tools exist, create new AIMessage for only them to be executed
        if non_hitl_tool_calls:
            new_ai_message = AIMessage(
                content=last_ai_message.content,
                tool_calls=non_hitl_tool_calls
            )
            return build_confirmation_result(
                all_tool_messages + [new_ai_message],
                False,
                non_hitl_call_ids,
                rejected
            )

        return build_confirmation_result(all_tool_messages, False, [], rejected)

    # case 3: partial approval
    # every tool_call in the original AIMessage needs a ToolMessage before any new AIMessage
    # add ToolMessages for all tool calls, then add a new AIMessage with approved tools
    all_tool_messages = approved_tool_msgs + rejected_tool_msgs + non_hitl_tool_msgs

    all_approved_ids = set(approved_ids) | set(non_hitl_call_ids)
    approved_tool_calls = [
        tc for tc in last_ai_message.tool_calls
        if tc['id'] in all_approved_ids
    ]
    new_ai_message = AIMessage(
        content=last_ai_message.content,
        tool_calls=approved_tool_calls
    )

    return build_confirmation_result(
        all_tool_messages + [new_ai_message],
        False,
        approved_ids + non_hitl_call_ids,
        rejected
    )


async def human_clarification(state: RequestState):
    """
    Human-in-the-loop clarification node.

    Interrupts execution to get user clarification when information is ambiguous.
    Handles remaining tool calls after clarification is received.
    """
    pending = state['pending_action']
    clarifications = pending['clarifications']
    clarification_call_ids = {c['call_id'] for c in clarifications}

    # interrupt and wait for user responses
    result = interrupt(None)

    # expected from /resume: {'responses': [{'call_id': '...', 'response': '...'}, ...]}
    responses = result.get('responses', [])
    response_map = {r['call_id']: r['response'] for r in responses}

    # create ToolMessages for each clarification
    clarification_msgs = [
        ToolMessage(
            content=f"User clarification: {response_map.get(c['call_id'], '')}",
            tool_call_id=c['call_id']
        )
        for c in clarifications
    ]

    last_ai = get_last_ai_message(state)
    remaining = [tc for tc in last_ai.tool_calls if tc['id'] not in clarification_call_ids]

    # no remaining tools - return to task_executor
    if not remaining:
        return {'messages': clarification_msgs, 'pending_action': NO_ACTION}

    # create dummy ToolMessages for deferred tools + new AIMessage
    dummy_msgs = create_tool_messages(
        [tc['id'] for tc in remaining],
        "Deferred pending clarification."
    )
    new_ai = AIMessage(content=last_ai.content, tool_calls=remaining)

    # check for HITL in remaining tools
    hitl_remaining = [tc for tc in remaining if tc['name'] in HITL_TOOLS]
    if hitl_remaining:
        return {
            'messages': clarification_msgs + dummy_msgs + [new_ai],
            'pending_action': {
                'kind': 'confirmation',
                'tool_calls': [
                    {'call_id': tc['id'], 'tool_name': tc['name'], 'arguments': tc['args']}
                    for tc in hitl_remaining
                ]
            }
        }

    return {
        'messages': clarification_msgs + dummy_msgs + [new_ai],
        'pending_action': NO_ACTION
    }


async def oauth_needed(state: RequestState):
    pending_action = state.get('pending_action', NO_ACTION)
    return {
        'final_response': pending_action.get('message', 'Authentication required.')
    }