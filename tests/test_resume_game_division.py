"""The `-HumanMilitary` switch: what it appends, and on which paths it appends.

`scripts\\resume-game.ps1 -HumanMilitary` is the human's switch for the division of labour: the human
commands the military units, the Great Generals and the Great Admirals, and the session owns every
other unit plus the cities, the economy, the wonders and the research. PowerShell cannot be driven from
pytest, so what is pinned here is the contract the script has to keep:

  * the switch exists, and the block is appended on **both** paths - the real launch and `-DryRun`,
    because a preview that lacks the division is a preview of a task the session would never receive;
  * the append is **idempotent** (the marker guard), so a second run against the same `-TaskFile` does
    not stack a second copy;
  * a missing task file is refused with a clear message instead of a raw `Select-String` error
    (measured 2026-10-05: `-DryRun -HumanMilitary -TaskFile <missing>` died inside the function with
    `Select-String : cannot find path` and printed no preview at all);
  * the appended text is ASCII with no BOM, because PowerShell 5.1 reads a BOM-less file as the ANSI
    code page, and the file carries Chinese save names elsewhere in the report;
  * the text still carries the clauses the division turns on, and still states the one fact a session
    gets fatally wrong if it is missing: `end_turn` does **not** refuse while a unit has movement.

The clauses are checked against the appended block only - a mention elsewhere in the script must not
satisfy them.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "resume-game.ps1"
MARKER = "## Division of labour: the human commands the military"


def source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def division_block(text: str | None = None) -> str:
    """The here-string appended to the task, without the script around it."""
    body = source() if text is None else text
    start = body.index("$division = @'\n") + len("$division = @'\n")
    end = body.index("\n'@", start)
    return body[start:end]


class TestTheFileItself:
    def test_it_is_pure_ascii_with_no_bom(self):
        raw = SCRIPT.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            "a BOM would be read as ANSI by PowerShell 5.1 alongside the rest of this file"
        )
        non_ascii = [b for b in raw if b > 127]
        assert not non_ascii, f"{len(non_ascii)} non-ASCII byte(s): this script must stay ASCII"

    def test_the_switch_exists(self):
        assert re.search(r"\[switch\]\s+\$HumanMilitary\b", source())


class TestWhereItAppends:
    def test_the_dry_run_appends_too(self):
        assert "if ($HumanMilitary) { $null = Add-DivisionOfLabour $taskFull }" in source(), (
            "-DryRun must preview the task a session would actually receive, division included"
        )
        assert "the division of labour is in the task above" in source()

    def test_the_real_launch_appends(self):
        body = source()
        assert re.search(r"^if \(\$HumanMilitary\) \{", body, re.M), "the real path has no call site"
        assert body.count("Add-DivisionOfLabour $taskFull") >= 2, (
            "both the preview and the launch have to append"
        )

    def test_the_append_is_idempotent(self):
        body = source()
        assert f"$marker = '{MARKER}'" in body
        assert "Select-String -Path $TaskPath -SimpleMatch -Pattern $marker -Quiet" in body
        assert "return $false" in body and "return $true" in body, (
            "the function reports whether it appended, and the launch path prints which happened"
        )

    def test_the_marker_check_comes_after_the_existence_guard(self):
        body = source()
        guard = body.index("if (-not (Test-Path $TaskPath))")
        select = body.index("Select-String -Path $TaskPath -SimpleMatch")
        assert guard < select, (
            "with $ErrorActionPreference='Stop' a missing file inside Select-String is a terminating "
            "error from inside the function: the guard has to come first"
        )
        assert "no task file to append the division to" in body

    def test_it_appends_rather_than_rewriting(self):
        assert "Add-Content -Path $TaskPath -Value $division -Encoding ASCII" in source()
        assert division_block().startswith("\n"), (
            "the block starts with a blank line so it cannot glue onto the task's last line"
        )


class TestTheTextItAppends:
    def test_it_names_both_halves(self):
        block = division_block()
        assert "Do not move a military unit. Do not move a Great General or a Great Admiral." in block
        assert "**Everything else is yours**" in block
        assert "the Great Scientists and the Great Merchants included" in block, (
            "the human's 2026-10-04 clarification: the Great Scientists and Great Merchants are the "
            "session's, not theirs"
        )

    def test_it_fixes_the_order_inside_a_turn(self):
        assert "You move first, every turn; the human moves after you." in division_block()

    def test_it_carries_the_whose_move_protocol(self):
        block = division_block()
        assert "`WHOSE MOVE|`" in block
        assert "agent-half.txt" in block
        assert "`agent working`" in block and "`your move`" in block and "`ready to end`" in block
        assert "`UI.CanEndTurn()` is not this fact" in block

    def test_it_carries_the_two_later_corrections(self):
        block = division_block()
        assert "A unit under a whole movement point is judged as skipped" in block, (
            "the sub-1-movement rule (human instruction 2026-10-04): without it a 0.2-move unit holds "
            "the report on YOUR MOVE after the game's own blocker has dropped"
        )
        assert "never call `skip_remaining_units()` at all" in block

    def test_it_states_that_end_turn_does_not_wait(self):
        block = division_block()
        assert "`end_turn` will not wait for the human - it discards their turn." in block
        assert "_sweep_unmoved_units" in block and "UNUSED ATTACK" in block

    def test_it_carries_the_stop_request_flow(self):
        block = division_block()
        assert "STOP REQUESTED|" in block
        assert "scripts\\stop-agent.py" in block
        assert "finish your own half" in block
