"""
Pytest configuration and fixtures for all tests.
Provides mock tools and fixtures decoupled from src definitions.
"""

import os
import pytest
from unittest.mock import patch
from langchain_core.tools import tool


# mock tool mapping to decouple from src TOOL_MAPPING
MOCK_TOOL_MAPPING = {
    'calendar': ['mock_list_calendars', 'mock_list_events', 'mock_create_event', 'mock_update_event'],
    'maps': ['mock_search_places', 'mock_get_directions'],
}

# mock HITL tools to decouple from src HITL_TOOLS
MOCK_HITL_TOOLS = {'mock_create_event', 'mock_update_event'}

# individual tool constants for unit tests
MOCK_HITL_TOOL = 'mock_hitl_tool'
MOCK_HITL_TOOL_2 = 'mock_hitl_tool_2'
MOCK_UNIT_HITL_TOOLS = {MOCK_HITL_TOOL, MOCK_HITL_TOOL_2}
MOCK_NON_HITL_TOOL = 'mock_non_hitl_tool'
MOCK_CLARIFICATION_TOOL = 'request_clarification'


# calendar mock tools
@tool
def mock_list_calendars() -> str:
    """List all available calendars."""
    return '[{"id": "primary", "summary": "Primary Calendar", "primary": true}]'


@tool
def mock_list_events(calendar_id: str, start_time: str = None, end_time: str = None) -> str:
    """List events from a calendar."""
    return '[{"id": "event1", "summary": "Team Meeting", "start": {"dateTime": "2024-01-15T10:00:00"}}]'


@tool
def mock_create_event(calendar_id: str, summary: str, start_time: str, end_time: str = None, description: str = None) -> str:
    """Create a new calendar event."""
    return '{"id": "new_event", "summary": "' + summary + '", "status": "confirmed"}'


@tool
def mock_update_event(calendar_id: str, event_id: str, summary: str = None, start_time: str = None, end_time: str = None) -> str:
    """Update an existing calendar event."""
    return '{"id": "' + event_id + '", "status": "updated"}'


# maps mock tools
@tool
def mock_search_places(query: str, location: str = None) -> str:
    """Search for places matching query."""
    return '[{"place_id": "place1", "name": "Coffee Shop", "address": "123 Main St"}]'


@tool
def mock_get_directions(origin: str, destination: str, mode: str = "driving") -> str:
    """Get directions between two locations."""
    return '{"distance": "5.2 km", "duration": "12 mins", "steps": ["Head north", "Turn right"]}'


MOCK_TOOLS = [
    mock_list_calendars,
    mock_list_events,
    mock_create_event,
    mock_update_event,
    mock_search_places,
    mock_get_directions,
]


@pytest.fixture(autouse=True)
def patch_hitl_tools():
    """Automatically patch HITL_TOOLS in the human module for all tests."""
    with patch('agentic.nodes.human.HITL_TOOLS', MOCK_UNIT_HITL_TOOLS):
        yield


@pytest.fixture(autouse=True)
def patch_tool_mapping():
    """Patches TOOL_MAPPING in agent.py and prompts.py to use mock tools."""
    with patch('agentic.nodes.agent.TOOL_MAPPING', MOCK_TOOL_MAPPING), \
         patch('agentic.schema.prompts.TOOL_MAPPING', MOCK_TOOL_MAPPING):
        yield


@pytest.fixture
def mock_mcp_client():
    """Patches CLIENT.get_tools to return mock tools, isolating LLM time from MCP latency."""
    async def mock_get_tools(server_name=None):
        return MOCK_TOOLS

    with patch('mcp_module.adapter.CLIENT.get_tools', new=mock_get_tools):
        yield MOCK_TOOLS


@pytest.fixture
def timing_threshold():
    """Returns max acceptable completion times in seconds for each node."""
    return {
        'policy_router': 5.0,
        'task_executor': 10.0
    }


@pytest.fixture
def verify_api_key():
    """Skips test if no API key is available."""
    openai_key = os.getenv('OPENAI_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')

    if not openai_key and not google_key:
        pytest.skip("No API key available (OPENAI_API_KEY or GOOGLE_API_KEY required)")

    return True
