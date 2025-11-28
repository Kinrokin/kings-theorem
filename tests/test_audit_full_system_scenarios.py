import pytest

from audit.full_system_audit import run_adversarial_scenarios
from tests.phase4_utils import configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def test_adversarial_scenarios_hold_their_invariants():
    failures = run_adversarial_scenarios()
    assert failures == 0, "Behavioral audit scenarios should not produce failures"
