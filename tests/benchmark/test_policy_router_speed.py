"""
Speed benchmark tests for policy_router node.
Measures single roundtrip LLM completion time.
"""

import time
import pytest
from langchain_core.messages import HumanMessage
from agentic.nodes.agent import policy_router


@pytest.mark.asyncio
async def test_item_request_speed(verify_api_key, timing_threshold):
    """Benchmark simple item routing request."""
    state = {
        'messages': [HumanMessage(content="What items do I have?")]
    }

    start = time.perf_counter()
    result = await policy_router(state)
    elapsed = time.perf_counter() - start

    print(f"\n[policy_router] item request: {elapsed:.3f}s")

    assert elapsed < timing_threshold['policy_router'], (
        f"policy_router took {elapsed:.3f}s, exceeds {timing_threshold['policy_router']}s threshold"
    )
    assert 'allowed_tool_types' in result


@pytest.mark.asyncio
async def test_refuse_request_speed(verify_api_key, timing_threshold):
    """Benchmark out-of-scope refusal routing."""
    state = {
        'messages': [HumanMessage(content="What's the weather like in New York?")]
    }

    start = time.perf_counter()
    result = await policy_router(state)
    elapsed = time.perf_counter() - start

    print(f"\n[policy_router] refuse request: {elapsed:.3f}s")

    assert elapsed < timing_threshold['policy_router'], (
        f"policy_router took {elapsed:.3f}s, exceeds {timing_threshold['policy_router']}s threshold"
    )
    assert 'allowed_tool_types' in result


@pytest.mark.asyncio
async def test_complex_request_speed(verify_api_key, timing_threshold):
    """Benchmark longer multi-sentence request."""
    state = {
        'messages': [HumanMessage(content=(
            "Create a new item called Quarterly Report for me. "
            "Also, can you check if I already have an item with that name? "
            "Update it if it exists."
        ))]
    }

    start = time.perf_counter()
    result = await policy_router(state)
    elapsed = time.perf_counter() - start

    print(f"\n[policy_router] complex request: {elapsed:.3f}s")

    assert elapsed < timing_threshold['policy_router'], (
        f"policy_router took {elapsed:.3f}s, exceeds {timing_threshold['policy_router']}s threshold"
    )
    assert 'allowed_tool_types' in result
