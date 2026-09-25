"""Test-wide isolation for the two files the turn-check machinery writes.

The checks are evaluated from a *file*, and anything that evaluates them can now also prune
the achieved goals out of it - `end_turn` calls the sweep as part of the turn. The default
path is the shipped `prompts/checks/turn-checks.md`, so a test that runs the hook against the
default path would edit the repository's own rule file (that happened: a test turn with a ram
in its fake army removed the live ram/tower goal from the real file).

Every test therefore gets a scratch copy of the shipped file at `CIV_MCP_TURN_CHECKS`, and a
scratch data directory at `CIV_MCP_DATA_DIR`, so retirement state cannot leak between tests
either. Tests that deliberately read the shipped file read it by path, and tests that install
their own file set the variable themselves - this fixture only changes the default.

The session teardown re-hashes the shipped file: if some future test writes to it anyway, the
suite fails loudly instead of quietly shipping a pruned directive.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import shutil
import uuid

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SHIPPED_CHECKS = REPO / "prompts" / "checks" / "turn-checks.md"


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def _shipped_checks_untouched():
    """Nothing in the suite may edit the repository's own check file."""
    before = _digest(SHIPPED_CHECKS)
    yield
    after = _digest(SHIPPED_CHECKS)
    assert after == before, (
        f"the test suite modified {SHIPPED_CHECKS} (sha256 {before[:12]} -> {after[:12]}); "
        "a test is writing to the shipped check file"
    )


@pytest.fixture(autouse=True)
def isolated_check_files(monkeypatch):
    """A per-test check file (the shipped one with retired goals restored) and a data directory.

    The shipped file is a moving target: a `once: true` goal leaves it the moment the game achieves
    it, and these tests are about the check machinery, not about which goals this playthrough has
    retired. Live, the ram/tower goal retired at T100 and turned five of them red twice on
    2026-09-25, for a game that was playing correctly.
    """
    from civ_mcp.turn_checks import restore_achieved

    root = REPO / ".tools" / f"_checks_env_{uuid.uuid4().hex}"
    checks = root / "turn-checks.md"
    data = root / "data"
    try:
        data.mkdir(parents=True)
        checks.write_text(
            restore_achieved(SHIPPED_CHECKS.read_text(encoding="utf-8")), encoding="utf-8"
        )
    except OSError:  # pragma: no cover - the copy is best effort, the paths still isolate
        root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CIV_MCP_TURN_CHECKS", str(checks))
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
    yield checks
    shutil.rmtree(root, ignore_errors=True)
