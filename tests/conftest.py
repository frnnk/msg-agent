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
    'example': ['mock_list_items', 'mock_get_item', 'mock_create_item', 'mock_update_item'],
    'lookup': ['mock_search', 'mock_fetch'],
}

# mock HITL tools to decouple from src HITL_TOOLS
MOCK_HITL_TOOLS = {'mock_create_item', 'mock_update_item'}

# individual tool constants for unit tests
MOCK_HITL_TOOL = 'mock_hitl_tool'
MOCK_HITL_TOOL_2 = 'mock_hitl_tool_2'
MOCK_UNIT_HITL_TOOLS = {MOCK_HITL_TOOL, MOCK_HITL_TOOL_2}
MOCK_NON_HITL_TOOL = 'mock_non_hitl_tool'
MOCK_CLARIFICATION_TOOL = 'request_clarification'


# example domain mock tools (read + HITL write)
@tool
def mock_list_items() -> str:
    """List all available items."""
    return '[{"id": "item-1", "name": "Example Item", "status": "active"}]'


@tool
def mock_get_item(item_id: str) -> str:
    """Get a single item by id."""
    return '{"id": "item-1", "name": "Example Item", "status": "active"}'


@tool
def mock_create_item(name: str, description: str = None) -> str:
    """Create a new item."""
    return '{"id": "new_item", "name": "' + name + '", "status": "created"}'


@tool
def mock_update_item(item_id: str, name: str = None) -> str:
    """Update an existing item."""
    return '{"id": "' + item_id + '", "status": "updated"}'


# lookup domain mock tools (read only)
@tool
def mock_search(query: str, filter: str = None) -> str:
    """Search for records matching a query."""
    return '[{"id": "result-1", "title": "Example Result"}]'


@tool
def mock_fetch(url: str) -> str:
    """Fetch content from a resource."""
    return '{"url": "https://example.com", "content": "Example content"}'


MOCK_TOOLS = [
    mock_list_items,
    mock_get_item,
    mock_create_item,
    mock_update_item,
    mock_search,
    mock_fetch,
]


@pytest.fixture(autouse=True)
def patch_hitl_tools():
    """Automatically patch HITL_TOOLS in the human and agent modules for all tests."""
    with patch('agentic.nodes.human.HITL_TOOLS', MOCK_UNIT_HITL_TOOLS), \
         patch('agentic.nodes.agent.HITL_TOOLS', MOCK_HITL_TOOLS):
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
        'task_executor': 16.0
    }


@pytest.fixture
def verify_api_key():
    """
    Skip the test unless a real LLM API key is configured.
    """
    # config.py injects placeholder keys so the package imports without a .env;
    # treat those sentinels as "no key" so real-LLM tests skip cleanly offline
    openai_key = os.getenv('OPENAI_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    has_real_key = any(
        key and 'PLACEHOLDER' not in key
        for key in (openai_key, google_key)
    )

    if not has_real_key:
        pytest.skip("No real API key available (OPENAI_API_KEY or GOOGLE_API_KEY required)")

    return True
