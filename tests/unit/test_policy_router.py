"""
Unit tests for policy_router node.
Tests both mock LLM (post-LLM logic) and real LLM (routing correctness).
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage
from agentic.nodes.agent import policy_router
from agentic.schema.models import PolicyRouterOut


def create_state(user_message: str) -> dict:
    """Create a minimal state with a user message."""
    return {
        'messages': [HumanMessage(content=user_message)]
    }


class TestPolicyRouterMockLLM:
    """
    Mock LLM tests for policy_router.
    Tests post-LLM logic by mocking the model's response.
    """
    @pytest.mark.asyncio
    async def test_calendar_allowed_extracts_tool_types(self):
        """Verify extraction when calendar tools are allowed."""
        mock_response = PolicyRouterOut(
            decision='allow',
            note='Calendar request detected',
            allowed_tool_types=['calendar']
        )

        mock_structured = MagicMock()
        mock_structured.ainvoke = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured)

        state = create_state("What's on my calendar?")
        with patch('agentic.nodes.agent.POLICY_ROUTER_MODEL', mock_model):
            result = await policy_router(state)

        assert result['allowed_tool_types'] == ['calendar']


    @pytest.mark.asyncio
    async def test_empty_allowed_types_on_refuse(self):
        """Verify empty list returned when request is refused."""
        mock_response = PolicyRouterOut(
            decision='refuse',
            note='Out of scope request',
            allowed_tool_types=[]
        )

        mock_structured = MagicMock()
        mock_structured.ainvoke = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured)

        state = create_state("What's the weather?")
        with patch('agentic.nodes.agent.POLICY_ROUTER_MODEL', mock_model):
            result = await policy_router(state)

        assert result['allowed_tool_types'] == []


    @pytest.mark.asyncio
    async def test_note_is_logged_not_returned(self):
        """Verify note field is not in returned state (only logged)."""
        mock_response = PolicyRouterOut(
            decision='allow',
            note='This note should not be in result',
            allowed_tool_types=['calendar']
        )

        mock_structured = MagicMock()
        mock_structured.ainvoke = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured)

        state = create_state("Show my calendar")
        with patch('agentic.nodes.agent.POLICY_ROUTER_MODEL', mock_model):
            result = await policy_router(state)

        assert 'note' not in result
        assert 'decision' not in result


    @pytest.mark.asyncio
    async def test_state_only_contains_allowed_tool_types(self):
        """Verify result only contains allowed_tool_types key."""
        mock_response = PolicyRouterOut(
            decision='allow',
            note='Test note',
            allowed_tool_types=['calendar']
        )

        mock_structured = MagicMock()
        mock_structured.ainvoke = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured)

        state = create_state("Test request")
        with patch('agentic.nodes.agent.POLICY_ROUTER_MODEL', mock_model):
            result = await policy_router(state)

        assert set(result.keys()) == {'allowed_tool_types', 'auth_url'}


class TestPolicyRouterRealLLM:
    """
    Real LLM tests for policy_router.
    Tests actual routing correctness with the configured model.
    """
    @pytest.mark.asyncio
    async def test_calendar_request_routes_to_calendar(self, verify_api_key):
        """Calendar viewing request should route to calendar tools."""
        state = create_state("What's on my calendar?")
        result = await policy_router(state)

        assert 'calendar' in result['allowed_tool_types']


    @pytest.mark.asyncio
    async def test_scheduling_request_routes_to_calendar(self, verify_api_key):
        """Scheduling request should route to calendar tools."""
        state = create_state("Schedule a meeting tomorrow at 3pm")
        result = await policy_router(state)

        assert 'calendar' in result['allowed_tool_types']


    @pytest.mark.asyncio
    async def test_out_of_scope_request_returns_empty(self, verify_api_key):
        """Out of scope request should return empty allowed_tool_types."""
        state = create_state("What's the weather in New York?")
        result = await policy_router(state)

        assert result['allowed_tool_types'] == []

    @pytest.mark.asyncio
    async def test_ambiguous_request_makes_decision(self, verify_api_key):
        """Ambiguous request should still return a valid decision."""
        state = create_state("Help me")
        result = await policy_router(state)

        # should return a valid list (could be empty or contain 'calendar')
        assert isinstance(result['allowed_tool_types'], list)
        for tool_type in result['allowed_tool_types']:
            assert tool_type in ['calendar']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
