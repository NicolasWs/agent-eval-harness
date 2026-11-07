"""Core runner: loads declarative test cases, runs them against an agent
adapter, checks assertions, and writes a JSON report.

Design: deliberately framework-agnostic. The "agent" is just anything with
a `.run(prompt: str) -> AgentResult`. Swap `MockAgent` for a real
OpenAI/Claude-based agent later without touching the runner or the cases.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class AgentResult:
    """What any agent adapter must return for a single turn."""
    output: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    latency_s: float = 0.0
    tokens_used: int | None = None


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    failures: list[str]
    agent_result: AgentResult


class Assertion:
    """One checkable expectation about an AgentResult. Subclass to add kinds."""

    def check(self, result: AgentResult) -> str | None:
        """Return None if it passes, else a human-readable failure reason."""
        raise NotImplementedError


class ContainsText(Assertion):
    def __init__(self, text: str, negate: bool = False):
        self.text = text
        self.negate = negate

    def check(self, result: AgentResult) -> str | None:
        hit = self.text.lower() in result.output.lower()
        if hit == self.negate:
            verb = "should not" if self.negate else "should"
            return f"output {verb} contain {self.text!r} — got: {result.output!r}"
        return None


class ToolCalled(Assertion):
    def __init__(self, tool_name: str, with_args: dict[str, Any] | None = None):
        self.tool_name = tool_name
        self.with_args = with_args or {}

    def check(self, result: AgentResult) -> str | None:
        matches = [c for c in result.tool_calls if c.get("name") == self.tool_name]
        if not matches:
            return f"expected tool {self.tool_name!r} to be called, none was"
        if self.with_args:
            for call in matches:
                if all(call.get("args", {}).get(k) == v for k, v in self.with_args.items()):
                    return None
            return f"tool {self.tool_name!r} called but never with args {self.with_args}"
        return None


class WithinBudget(Assertion):
    def __init__(self, max_latency_s: float | None = None, max_tokens: int | None = None):
        self.max_latency_s = max_latency_s
        self.max_tokens = max_tokens

    def check(self, result: AgentResult) -> str | None:
        if self.max_latency_s is not None and result.latency_s > self.max_latency_s:
            return f"latency {result.latency_s:.2f}s exceeded budget {self.max_latency_s}s"
        if self.max_tokens is not None and (result.tokens_used or 0) > self.max_tokens:
            return f"tokens {result.tokens_used} exceeded budget {self.max_tokens}"
        return None


ASSERTION_KINDS: dict[str, Callable[..., Assertion]] = {
    "contains_text": lambda **kw: ContainsText(**kw),
    "tool_called": lambda **kw: ToolCalled(**kw),
    "within_budget": lambda **kw: WithinBudget(**kw),
}


def load_case(path: Path) -> dict[str, Any]:
    import yaml  # local import keeps `harness` importable without pyyaml for pure-Python use

    return yaml.safe_load(path.read_text())


def build_assertions(spec: list[dict[str, Any]]) -> list[Assertion]:
    out = []
    for item in spec:
        kind = item["kind"]
        kwargs = {k: v for k, v in item.items() if k != "kind"}
        out.append(ASSERTION_KINDS[kind](**kwargs))
    return out


def run_case(case: dict[str, Any], agent: Any) -> CaseResult:
    start = time.monotonic()
    result = agent.run(case["prompt"])
    if not result.latency_s:
        result.latency_s = time.monotonic() - start

    failures = []
    for assertion in build_assertions(case.get("assertions", [])):
        failure = assertion.check(result)
        if failure:
            failures.append(failure)

    return CaseResult(
        case_id=case["id"],
        passed=not failures,
        failures=failures,
        agent_result=result,
    )


def run_all(cases_dir: Path, agent: Any, report_path: Path | None = None) -> list[CaseResult]:
    results = []
    for case_file in sorted(cases_dir.glob("*.yaml")):
        case = load_case(case_file)
        results.append(run_case(case, agent))

    if report_path:
        report_path.write_text(json.dumps(
            [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "failures": r.failures,
                    "output": r.agent_result.output,
                }
                for r in results
            ],
            indent=2,
        ))
    return results
