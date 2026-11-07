"""A trivial scripted agent, just enough to exercise the harness end to end
without any API key. Swap this for a real adapter in v1 (see README roadmap).
"""
from __future__ import annotations

from .runner import AgentResult


class MockAgent:
    """Returns canned answers and fake tool calls keyed by prompt content.

    v1 replaces this with e.g. an OpenAIAgent/ClaudeAgent adapter that calls
    the real model and real tools, but keeps the exact same `.run()` contract
    so none of the test cases or the runner need to change.
    """

    def run(self, prompt: str) -> AgentResult:
        prompt_l = prompt.lower()

        if "weather" in prompt_l:
            return AgentResult(
                output="It's 14°C and cloudy in Paris today.",
                tool_calls=[{"name": "get_weather", "args": {"city": "Paris"}}],
                tokens_used=42,
            )

        if "refund" in prompt_l:
            # Deliberately wrong behaviour: agent should call a tool but doesn't.
            return AgentResult(output="Sure, I've refunded your order.", tool_calls=[])

        return AgentResult(output="I'm not sure how to help with that.", tokens_used=12)
