"""Every route-A driver has to at least start.

Measured 2026-10-07: `scripts/record-turn.py` - the script that writes a script-driven turn into the
run's diary - died with `NameError: name 'ROOT' is not defined` at line 42, before its argument
parser ran, so **every** invocation failed and the diary for T363-T369 was never written. A driver
that cannot answer `--help` is a driver nobody can use, and the failure is invisible from the outside
(the session that would have written the row simply had no row).
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Scripts that are invoked with subcommands and flags but must still answer `--help` and exit 0.
DRIVERS = ("record-turn.py",)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / args[0]), *args[1:]],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )


class TestTheRouteADriversStart:
    @pytest.mark.parametrize("script", DRIVERS)
    def test_help_is_available(self, script: str):
        done = _run(script, "--help")
        assert done.returncode == 0, (done.stdout or "") + (done.stderr or "")
        assert "usage:" in (done.stdout or ""), done.stdout

    def test_record_turn_show_reads_the_run_diary(self):
        """`--show` exercises the module-level data directory and the run resolution, not the game."""
        done = _run("record-turn.py", "--show", "--tail", "1")
        assert done.returncode == 0, (done.stdout or "") + (done.stderr or "")
        assert "row(s)" in (done.stdout or ""), done.stdout
