"""
Unit tests for human_confirmation node with mixed HITL and non-HITL tools.
Tests the fix for handling non-HITL tools alongside HITL tools in the same AIMessage.
"""

import pytest
from unittest.mock import patch
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from agentic.nodes.human import human_confirmation
from agentic.state import NO_ACTION


def create_mock_state(tool_calls: list, pending_tool_calls: list) -> dict:
    """Create a mock state with an AIMessage containing the given tool calls."""
    ai_message = AIMessage(
        content="I'll help you with that.",
        tool_calls=tool_calls
    )
    return {
        'messages': [HumanMessage(content="test"), ai_message],
        'pending_action': {
            'kind': 'confirmation',
            'tool_calls': pending_tool_calls # pending state with only hitl tools
        }
    }


class TestMixedToolCalls:
    """
    Test cases for AIMessages with both HITL and non-HITL tools
    """
    @pytest.mark.asyncio
    async def test_case1_all_approved_unchanged(self):
        """Case 1: All approved (no new messages)"""
        tool_calls = [
            {'id': 'call_hitl_1', 'name': 'create_event', 'args': {'name': 'Test'}},
            {'id': 'call_non_hitl_1', 'name': 'list_calendars', 'args': {}},
        ]
        pending_tool_calls = [
            {'call_id': 'call_hitl_1', 'tool_name': 'create_event', 'arguments': {'name': 'Test'}}
        ]
        state = create_mock_state(tool_calls, pending_tool_calls)

        approval_results = [{'call_id': 'call_hitl_1', 'approved': True}]
        with patch('agentic.nodes.human.interrupt', return_value=approval_results):
            result = await human_confirmation(state)

        # case 1 should not add any messages, leave messages untouched
        assert 'messages' not in result or result.get('messages') is None
        assert result['approval_outcome']['all_approved'] is True


    @pytest.mark.asyncio
    async def test_case2_all_rejected_with_non_hitl(self):
        """Case 2: All HITL rejected, but non-HITL tools should still execute"""
        tool_calls = [
            {'id': 'call_hitl_1', 'name': 'create_event', 'args': {'name': 'Test'}},
            {'id': 'call_non_hitl_1', 'name': 'list_calendars', 'args': {}},
            {'id': 'call_non_hitl_2', 'name': 'list_calendars', 'args': {}},
        ]
        pending_tool_calls = [
            {'call_id': 'call_hitl_1', 'tool_name': 'create_event', 'arguments': {'name': 'Test'}}
        ]
        state = create_mock_state(tool_calls, pending_tool_calls)

        approval_results = [{'call_id': 'call_hitl_1', 'approved': False, 'feedback': 'Wrong name'}]
        with patch('agentic.nodes.human.interrupt', return_value=approval_results):
            result = await human_confirmation(state)
        messages = result['messages']

        # verify that we have constructed filler ToolMessages for both tools
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 3, "Should have ToolMessages for both HITL and non-HITL"

        # verify we have constructed a new AIMessage with only the 2 non-HITL tools
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        assert len(ai_messages) == 1, "Should create new AIMessage for non-HITL tools"
        assert len(ai_messages[0].tool_calls) == 2

        # approved_call_ids should include non-HITL for routing
        assert 'call_non_hitl_1' in result['approval_outcome']['approved_call_ids']
        assert 'call_non_hitl_2' in result['approval_outcome']['approved_call_ids']


    @pytest.mark.asyncio
    async def test_case2_all_rejected_no_non_hitl(self):
        """Case 2: All HITL rejected, no non-HITL tools"""
        tool_calls = [
            {'id': 'call_hitl_1', 'name': 'create_event', 'args': {'name': 'Test'}},
        ]
        pending_tool_calls = [
            {'call_id': 'call_hitl_1', 'tool_name': 'create_event', 'arguments': {'name': 'Test'}}
        ]
        state = create_mock_state(tool_calls, pending_tool_calls)

        approval_results = [{'call_id': 'call_hitl_1', 'approved': False, 'feedback': 'No'}]
        with patch('agentic.nodes.human.interrupt', return_value=approval_results):
            result = await human_confirmation(state)

        messages = result['messages']
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        assert len(tool_messages) == 1, "Should only have ToolMessage for rejected HITL"
        assert len(ai_messages) == 0, "Should not create new AIMessage"
        assert result['approval_outcome']['approved_call_ids'] == []


    @pytest.mark.asyncio
    async def test_case3_partial_with_non_hitl(self):
        """Case 3: Partial HITL approval with non-HITL tools."""
        tool_calls = [
            {'id': 'call_hitl_1', 'name': 'create_event', 'args': {'name': 'Event 1'}},
            {'id': 'call_hitl_2', 'name': 'update_event', 'args': {'name': 'Event 2'}},
            {'id': 'call_non_hitl_1', 'name': 'list_calendars', 'args': {}},
        ]
        pending_tool_calls = [
            {'call_id': 'call_hitl_1', 'tool_name': 'create_event', 'arguments': {'name': 'Event 1'}},
            {'call_id': 'call_hitl_2', 'tool_name': 'update_event', 'arguments': {'name': 'Event 2'}},
        ]
        state = create_mock_state(tool_calls, pending_tool_calls)

        approval_results = [
            {'call_id': 'call_hitl_1', 'approved': True},
            {'call_id': 'call_hitl_2', 'approved': False, 'feedback': 'Skip this'},
        ]
        with patch('agentic.nodes.human.interrupt', return_value=approval_results):
            result = await human_confirmation(state)
        messages = result['messages']

        # verify filler ToolMessages created for each tool
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 3, "Should have ToolMessages for all tools"

        # new AIMessage should have approved HITL + non-HITL tools
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        assert len(ai_messages) == 1, "Only one AIMessage created with approved tools"
        new_tool_ids = {tc['id'] for tc in ai_messages[0].tool_calls}
        assert new_tool_ids == {'call_hitl_1', 'call_non_hitl_1'}

        # approved_call_ids should include both approved HITL and non-HITL
        approved_ids = result['approval_outcome']['approved_call_ids']
        assert 'call_hitl_1' in approved_ids
        assert 'call_non_hitl_1' in approved_ids
        assert 'call_hitl_2' not in approved_ids


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
