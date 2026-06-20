"""
Speed benchmark tests for task_executor node.
Measures single roundtrip LLM completion time.
"""

import time
import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agentic.nodes.agent import task_executor


@pytest.mark.asyncio
async def test_list_items_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark query items request."""
    state = {
        'messages': [HumanMessage(content="What items do I have?")],
        'allowed_tool_types': ['example']
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] list items: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result


@pytest.mark.asyncio
async def test_create_item_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark HITL tool invocation request."""
    state = {
        'messages': [HumanMessage(content="Create an item called Quarterly Report")],
        'allowed_tool_types': ['example']
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] create item: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result


@pytest.mark.asyncio
async def test_ambiguous_request_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark ambiguous request that may trigger clarification."""
    state = {
        'messages': [HumanMessage(content="Create something")],
        'allowed_tool_types': ['example']
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] ambiguous request: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result


@pytest.mark.asyncio
async def test_multi_turn_context_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark multi-turn conversation with tool results in context."""
    state = {
        'messages': [
            HumanMessage(content="What items do I have?"),
            AIMessage(
                content="",
                tool_calls=[{
                    'id': 'call_list_items',
                    'name': 'list_items',
                    'args': {}
                }]
            ),
            ToolMessage(
                content='[{"id": "item-1", "name": "Example Item", "status": "active"}]',
                tool_call_id='call_list_items'
            ),
            AIMessage(
                content="",
                tool_calls=[{
                    'id': 'call_get_item',
                    'name': 'get_item',
                    'args': {'item_id': 'item-1'}
                }]
            ),
            ToolMessage(
                content='{"id": "item-1", "name": "Example Item", "status": "active"}',
                tool_call_id='call_get_item'
            )
        ],
        'allowed_tool_types': ['example']
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] multi-turn context: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result


@pytest.mark.asyncio
async def test_no_tools_allowed_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark out-of-scope request with empty allowed_tools (final response path)."""
    state = {
        'messages': [HumanMessage(content="What's the weather like in New York?")],
        'allowed_tool_types': []
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] no tools allowed: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result
