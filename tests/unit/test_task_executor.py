"""
Unit tests for task_executor node.
Tests post-LLM routing logic by mocking the model's response.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage
from agentic.nodes.agent import task_executor
from tests.conftest import MOCK_TOOLS


# sample tool call constants for unit tests
SAMPLE_CLARIFICATION_CALL = {
    'id': 'call_clarify_1',
    'name': 'request_clarification',
    'args': {'question': 'What time?', 'context': 'Scheduling meeting'}
}

SAMPLE_HITL_CALL = {
    'id': 'call_create_1',
    'name': 'mock_create_event',
    'args': {'calendar_id': 'primary', 'summary': 'Meeting', 'start_time': '2024-01-15T10:00:00'}
}

SAMPLE_NON_HITL_CALL = {
    'id': 'call_list_1',
    'name': 'mock_list_events',
    'args': {'calendar_id': 'primary'}
}

def create_state(user_message: str, allowed_tool_types: list = None) -> dict:
    """Create a minimal state for task_executor."""
    return {
        'messages': [HumanMessage(content=user_message)],
        'allowed_tool_types': allowed_tool_types or ['calendar']
    }


def create_mock_ai_message(content: str, tool_calls: list = None) -> AIMessage:
    """Create a mock AIMessage with optional tool calls."""
    return AIMessage(content=content, tool_calls=tool_calls or [])


async def mock_get_tools():
    """Mock CLIENT.get_tools to return mock tools."""
    return MOCK_TOOLS


class TestClarificationRouting:
    """
    Tests for clarification request detection and routing.
    Clarification takes priority over HITL tools.
    """
    @pytest.mark.asyncio
    async def test_single_clarification_sets_pending_action(self):
        """Single clarification call sets pending_action.kind='clarification'."""
        mock_message = create_mock_ai_message(
            content="I need more information.",
            tool_calls=[SAMPLE_CLARIFICATION_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Schedule something")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert result['pending_action']['kind'] == 'clarification'
        assert len(result['pending_action']['clarifications']) == 1


    @pytest.mark.asyncio
    async def test_multiple_clarifications_all_captured(self):
        """Multiple clarification calls are all captured in the list."""
        clarification_call_1 = {
            'id': 'call_clarify_1',
            'name': 'request_clarification',
            'args': {'question': 'What time?', 'context': 'Time needed'}
        }
        clarification_call_2 = {
            'id': 'call_clarify_2',
            'name': 'request_clarification',
            'args': {'question': 'Which calendar?', 'context': 'Calendar selection'}
        }
        mock_message = create_mock_ai_message(
            content="I need clarification.",
            tool_calls=[clarification_call_1, clarification_call_2]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Schedule a meeting")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert len(result['pending_action']['clarifications']) == 2
        call_ids = [c['call_id'] for c in result['pending_action']['clarifications']]
        assert 'call_clarify_1' in call_ids
        assert 'call_clarify_2' in call_ids


    @pytest.mark.asyncio
    async def test_clarification_extracts_question_and_context(self):
        """Verify call_id, question, and context are correctly extracted."""
        mock_message = create_mock_ai_message(
            content="Need info.",
            tool_calls=[SAMPLE_CLARIFICATION_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Do something")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        clarification = result['pending_action']['clarifications'][0]
        assert clarification['call_id'] == 'call_clarify_1'
        assert clarification['question'] == 'What time?'
        assert clarification['context'] == 'Scheduling meeting'


    @pytest.mark.asyncio
    async def test_clarification_priority_over_hitl(self):
        """Clarification takes priority when mixed with HITL tools."""
        mock_message = create_mock_ai_message(
            content="I'll create the event but need more info.",
            tool_calls=[SAMPLE_CLARIFICATION_CALL, SAMPLE_HITL_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Schedule a meeting")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        # should route to clarification, not confirmation
        assert result['pending_action']['kind'] == 'clarification'
        assert 'tool_calls' not in result['pending_action']


class TestHITLRouting:
    """
    Tests for HITL (human-in-the-loop) tool detection and routing.
    """
    @pytest.mark.asyncio
    async def test_single_hitl_sets_confirmation_pending(self):
        """Single HITL tool call sets pending_action.kind='confirmation'."""
        mock_message = create_mock_ai_message(
            content="Creating event.",
            tool_calls=[SAMPLE_HITL_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Create a meeting")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert result['pending_action']['kind'] == 'confirmation'
        assert len(result['pending_action']['tool_calls']) == 1


    @pytest.mark.asyncio
    async def test_multiple_hitl_all_captured(self):
        """Multiple HITL tools are all captured in tool_calls."""
        hitl_call_1 = {
            'id': 'call_create_1',
            'name': 'mock_create_event',
            'args': {'calendar_id': 'primary', 'summary': 'Meeting 1'}
        }
        hitl_call_2 = {
            'id': 'call_update_1',
            'name': 'mock_update_event',
            'args': {'calendar_id': 'primary', 'event_id': 'evt1', 'summary': 'Updated'}
        }
        mock_message = create_mock_ai_message(
            content="Managing events.",
            tool_calls=[hitl_call_1, hitl_call_2]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Create and update events")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert len(result['pending_action']['tool_calls']) == 2
        call_ids = [tc['call_id'] for tc in result['pending_action']['tool_calls']]
        assert 'call_create_1' in call_ids
        assert 'call_update_1' in call_ids


    @pytest.mark.asyncio
    async def test_hitl_extracts_call_info(self):
        """Verify call_id, tool_name, and arguments are correctly extracted."""
        mock_message = create_mock_ai_message(
            content="Creating event.",
            tool_calls=[SAMPLE_HITL_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Create a meeting")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        tool_call = result['pending_action']['tool_calls'][0]
        assert tool_call['call_id'] == 'call_create_1'
        assert tool_call['tool_name'] == 'mock_create_event'
        assert tool_call['arguments']['calendar_id'] == 'primary'
        assert tool_call['arguments']['summary'] == 'Meeting'


    @pytest.mark.asyncio
    async def test_mixed_hitl_non_hitl_only_hitl_in_pending(self):
        """Mixed HITL and non-HITL tools: only HITL appear in pending_action."""
        mock_message = create_mock_ai_message(
            content="Listing and creating.",
            tool_calls=[SAMPLE_HITL_CALL, SAMPLE_NON_HITL_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Show calendar and create event")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert result['pending_action']['kind'] == 'confirmation'
        
        # only HITL tools should be in pending_action
        tool_names = [tc['tool_name'] for tc in result['pending_action']['tool_calls']]
        assert 'mock_create_event' in tool_names
        assert 'mock_list_events' not in tool_names


class TestNoToolCalls:
    """
    Tests for when LLM responds without tool calls.
    """
    @pytest.mark.asyncio
    async def test_no_tools_sets_final_response(self):
        """No tool calls sets final_response in state."""
        mock_message = create_mock_ai_message(
            content="Here's what's on your calendar today.",
            tool_calls=[]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("What's on my calendar?")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert result['final_response'] == "Here's what's on your calendar today."


    @pytest.mark.asyncio
    async def test_no_tools_includes_message_in_state(self):
        """Message is included in state when no tool calls."""
        mock_message = create_mock_ai_message(
            content="Here's the response.",
            tool_calls=[]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Tell me about my day")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert 'messages' in result
        assert result['messages'].content == "Here's the response."


class TestRegularToolCalls:
    """
    Tests for non-HITL tool calls (no confirmation required).
    """
    @pytest.mark.asyncio
    async def test_non_hitl_tools_returns_message_only(self):
        """Non-HITL tools return message without pending_action."""
        mock_message = create_mock_ai_message(
            content="Listing events.",
            tool_calls=[SAMPLE_NON_HITL_CALL]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Show my events")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert 'messages' in result
        assert 'pending_action' not in result
        assert 'final_response' not in result


    @pytest.mark.asyncio
    async def test_multiple_non_hitl_tools(self):
        """Multiple non-HITL tools return message without pending_action."""
        non_hitl_call_1 = {
            'id': 'call_list_1',
            'name': 'mock_list_events',
            'args': {'calendar_id': 'primary'}
        }
        non_hitl_call_2 = {
            'id': 'call_list_calendars_1',
            'name': 'mock_list_calendars',
            'args': {}
        }
        mock_message = create_mock_ai_message(
            content="Getting calendar info.",
            tool_calls=[non_hitl_call_1, non_hitl_call_2]
        )

        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_message)

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_bound)

        state = create_state("Show all calendars and events")
        with patch('agentic.nodes.agent.TASK_EXECUTOR_MODEL', mock_model), \
             patch('agentic.nodes.agent.CLIENT.get_tools', mock_get_tools):
            result = await task_executor(state)

        assert 'messages' in result
        assert len(result['messages'].tool_calls) == 2
        assert 'pending_action' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
