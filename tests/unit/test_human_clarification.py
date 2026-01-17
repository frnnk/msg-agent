"""
Unit tests for human_clarification node handling clarification requests.
Tests various scenarios including clarification-only, mixed with HITL, and mixed with non-HITL tools.
"""

import pytest
from unittest.mock import patch
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from agentic.nodes.human import human_clarification
from agentic.state import NO_ACTION
from tests.conftest import MOCK_HITL_TOOL, MOCK_NON_HITL_TOOL


def create_mock_state(tool_calls: list, pending_clarifications: list) -> dict:
    """Create a mock state with an AIMessage containing the given tool calls."""
    ai_message = AIMessage(
        content="I need some clarification.",
        tool_calls=tool_calls
    )
    return {
        'messages': [HumanMessage(content="test"), ai_message],
        'pending_action': {
            'kind': 'clarification',
            'clarifications': pending_clarifications
        }
    }


class TestSingleClarification:
    """Test cases for single clarification request with no other tools."""

    @pytest.mark.asyncio
    async def test_single_clarification_no_other_tools(self):
        """Single clarification with no remaining tools should return to task_executor."""
        tool_calls = [
            {'id': 'call_clarify_1', 'name': 'request_clarification', 'args': {'question': 'What time?'}}
        ]
        pending_clarifications = [
            {'call_id': 'call_clarify_1', 'question': 'What time?', 'context': ''}
        ]
        state = create_mock_state(tool_calls, pending_clarifications)

        responses = {'responses': [{'call_id': 'call_clarify_1', 'response': '3pm'}]}
        with patch('agentic.nodes.human.interrupt', return_value=responses):
            result = await human_clarification(state)

        messages = result['messages']
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 1
        assert 'User clarification: 3pm' in tool_messages[0].content
        assert result['pending_action'] == NO_ACTION


class TestMultipleClarifications:
    """Test cases for multiple clarification requests with no other tools."""

    @pytest.mark.asyncio
    async def test_multiple_clarifications_no_other_tools(self):
        """Multiple clarifications with no remaining tools should return to task_executor."""
        tool_calls = [
            {'id': 'call_clarify_1', 'name': 'request_clarification', 'args': {'question': 'What time?'}},
            {'id': 'call_clarify_2', 'name': 'request_clarification', 'args': {'question': 'Which day?'}}
        ]
        pending_clarifications = [
            {'call_id': 'call_clarify_1', 'question': 'What time?', 'context': ''},
            {'call_id': 'call_clarify_2', 'question': 'Which day?', 'context': ''}
        ]
        state = create_mock_state(tool_calls, pending_clarifications)

        responses = {
            'responses': [
                {'call_id': 'call_clarify_1', 'response': '3pm'},
                {'call_id': 'call_clarify_2', 'response': 'tomorrow'}
            ]
        }
        with patch('agentic.nodes.human.interrupt', return_value=responses):
            result = await human_clarification(state)

        messages = result['messages']
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 2
        assert result['pending_action'] == NO_ACTION


class TestClarificationWithNonHITL:
    """Test cases for clarification with non-HITL tools."""

    @pytest.mark.asyncio
    async def test_clarification_with_non_hitl_tools(self):
        """Clarification + non-HITL tools should route to use_tools."""
        tool_calls = [
            {'id': 'call_clarify_1', 'name': 'request_clarification', 'args': {'question': 'What time?'}},
            {'id': 'call_non_hitl_1', 'name': MOCK_NON_HITL_TOOL, 'args': {}}
        ]
        pending_clarifications = [
            {'call_id': 'call_clarify_1', 'question': 'What time?', 'context': ''}
        ]
        state = create_mock_state(tool_calls, pending_clarifications)

        responses = {'responses': [{'call_id': 'call_clarify_1', 'response': '3pm'}]}
        with patch('agentic.nodes.human.interrupt', return_value=responses):
            result = await human_clarification(state)

        messages = result['messages']
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        # should have clarification ToolMessage + dummy ToolMessage for deferred
        assert len(tool_messages) == 2
        # should have new AIMessage with remaining tools
        assert len(ai_messages) == 1
        assert len(ai_messages[0].tool_calls) == 1
        assert ai_messages[0].tool_calls[0]['name'] == MOCK_NON_HITL_TOOL
        # should return to use_tools (no confirmation pending)
        assert result['pending_action'] == NO_ACTION


class TestClarificationWithHITL:
    """Test cases for clarification with HITL tools."""

    @pytest.mark.asyncio
    async def test_clarification_with_hitl_tools(self):
        """Clarification + HITL tools should route to human_confirmation."""
        tool_calls = [
            {'id': 'call_clarify_1', 'name': 'request_clarification', 'args': {'question': 'What time?'}},
            {'id': 'call_hitl_1', 'name': MOCK_HITL_TOOL, 'args': {'name': 'Meeting'}}
        ]
        pending_clarifications = [
            {'call_id': 'call_clarify_1', 'question': 'What time?', 'context': ''}
        ]
        state = create_mock_state(tool_calls, pending_clarifications)

        responses = {'responses': [{'call_id': 'call_clarify_1', 'response': '3pm'}]}
        with patch('agentic.nodes.human.interrupt', return_value=responses):
            result = await human_clarification(state)

        messages = result['messages']
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        assert len(ai_messages) == 1
        assert ai_messages[0].tool_calls[0]['name'] == MOCK_HITL_TOOL
        # should route to human_confirmation
        assert result['pending_action']['kind'] == 'confirmation'
        assert len(result['pending_action']['tool_calls']) == 1
        assert result['pending_action']['tool_calls'][0]['tool_name'] == MOCK_HITL_TOOL


class TestClarificationWithMixedTools:
    """Test cases for clarification with both HITL and non-HITL tools."""

    @pytest.mark.asyncio
    async def test_clarification_with_mixed_tools(self):
        """Clarification + HITL + non-HITL tools should route to human_confirmation."""
        tool_calls = [
            {'id': 'call_clarify_1', 'name': 'request_clarification', 'args': {'question': 'What time?'}},
            {'id': 'call_hitl_1', 'name': MOCK_HITL_TOOL, 'args': {'name': 'Meeting'}},
            {'id': 'call_non_hitl_1', 'name': MOCK_NON_HITL_TOOL, 'args': {}}
        ]
        pending_clarifications = [
            {'call_id': 'call_clarify_1', 'question': 'What time?', 'context': ''}
        ]
        state = create_mock_state(tool_calls, pending_clarifications)

        responses = {'responses': [{'call_id': 'call_clarify_1', 'response': '3pm'}]}
        with patch('agentic.nodes.human.interrupt', return_value=responses):
            result = await human_clarification(state)

        messages = result['messages']
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        # new AIMessage should have both HITL and non-HITL tools
        assert len(ai_messages) == 1
        tool_names = {tc['name'] for tc in ai_messages[0].tool_calls}
        assert tool_names == {MOCK_HITL_TOOL, MOCK_NON_HITL_TOOL}

        # pending_action should only have HITL tools for confirmation
        assert result['pending_action']['kind'] == 'confirmation'
        assert len(result['pending_action']['tool_calls']) == 1
        assert result['pending_action']['tool_calls'][0]['tool_name'] == MOCK_HITL_TOOL


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
