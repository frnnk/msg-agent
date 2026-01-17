"""
Pytest configuration and fixtures for HITL tests.
Decouples tests from actual HITL_TOOLS by patching with mock tool names.
"""

import pytest
from unittest.mock import patch

# mock tool constants used across all tests
MOCK_HITL_TOOL = 'mock_hitl_tool'
MOCK_HITL_TOOL_2 = 'mock_hitl_tool_2'
MOCK_HITL_TOOLS = {MOCK_HITL_TOOL, MOCK_HITL_TOOL_2}
MOCK_NON_HITL_TOOL = 'mock_non_hitl_tool'
MOCK_CLARIFICATION_TOOL = 'request_clarification'


@pytest.fixture(autouse=True)
def patch_hitl_tools():
    """Automatically patch HITL_TOOLS in the human module for all tests."""
    with patch('agentic.nodes.human.HITL_TOOLS', MOCK_HITL_TOOLS):
        yield
