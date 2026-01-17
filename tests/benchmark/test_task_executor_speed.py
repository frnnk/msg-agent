"""
Speed benchmark tests for task_executor node.
Measures single roundtrip LLM completion time.
"""

import time
import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agentic.nodes.agent import task_executor


@pytest.mark.asyncio
async def test_list_events_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark query events request."""
    state = {
        'messages': [HumanMessage(content="What's on my calendar today?")],
        'allowed_tool_types': ['calendar']
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] list events: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result


@pytest.mark.asyncio
async def test_create_event_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark HITL tool invocation request."""
    state = {
        'messages': [HumanMessage(content="Schedule a dentist appointment tomorrow at 2pm")],
        'allowed_tool_types': ['calendar']
    }

    start = time.perf_counter()
    result = await task_executor(state)
    elapsed = time.perf_counter() - start

    print(f"\n[task_executor] create event: {elapsed:.3f}s")

    assert elapsed < timing_threshold['task_executor'], (
        f"task_executor took {elapsed:.3f}s, exceeds {timing_threshold['task_executor']}s threshold"
    )
    assert 'messages' in result


@pytest.mark.asyncio
async def test_ambiguous_request_speed(verify_api_key, mock_mcp_client, timing_threshold):
    """Benchmark ambiguous request that may trigger clarification."""
    state = {
        'messages': [HumanMessage(content="Schedule something")],
        'allowed_tool_types': ['calendar']
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
            HumanMessage(content="What's on my calendar today?"),
            AIMessage(
                content="",
                tool_calls=[{
                    'id': 'call_list_calendars',
                    'name': 'list_calendars',
                    'args': {}
                }]
            ),
            ToolMessage(
                content='[{"id": "primary", "summary": "Primary Calendar", "primary": true}]',
                tool_call_id='call_list_calendars'
            ),
            AIMessage(
                content="",
                tool_calls=[{
                    'id': 'call_list_events',
                    'name': 'list_events',
                    'args': {'calendar_id': 'primary'}
                }]
            ),
            ToolMessage(
                content='[{"id": "event1", "summary": "Team Meeting", "start": {"dateTime": "2024-01-15T10:00:00"}}]',
                tool_call_id='call_list_events'
            )
        ],
        'allowed_tool_types': ['calendar']
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
