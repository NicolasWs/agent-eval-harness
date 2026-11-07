from pathlib import Path

from harness.mock_agent import MockAgent
from harness.runner import run_all

CASES_DIR = Path(__file__).parent / "cases"
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def test_weather_case_passes():
    results = run_all(CASES_DIR, MockAgent())
    weather = next(r for r in results if r.case_id == "weather_tool_call")
    assert weather.passed, weather.failures


def test_refund_case_catches_missing_tool_call():
    """Demonstrates the harness catching a real agent failure mode."""
    results = run_all(CASES_DIR, MockAgent())
    refund = next(r for r in results if r.case_id == "refund_requires_tool")
    assert not refund.passed
    assert "process_refund" in refund.failures[0]


def test_report_is_written():
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / "latest.json"
    run_all(CASES_DIR, MockAgent(), report_path=report_path)
    assert report_path.exists()
