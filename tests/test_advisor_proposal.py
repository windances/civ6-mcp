"""The worker-proposal contract, tested the way the orchestrator has to apply it.

A proposal is only actionable if it is schema-valid, names tools and arguments that exist, cites
units that are in the snapshot the worker was given, and has unique action ids. Phase 3 of the
skill says to reject anything else, and `.tools/verify-advisor-proposal.py` is that rejection
made runnable. These cases pin the two controls (a well-formed proposal and a deliberately broken
one) plus the snapshot contract, without spawning the MCP server for the tool inventory
(`--no-inventory`), which the gate already checks separately.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
SCRIPT = REPO / ".tools" / "verify-advisor-proposal.py"


def run(*args: str, inventory: bool = True) -> subprocess.CompletedProcess:
    """Run the validator. `inventory=False` skips the tool checks entirely.

    With `inventory=True` the tool list comes from `tests/fixtures/mcp-tool-inventory.json`
    rather than from spawning the MCP server, so the tool and argument checks are pinned
    deterministically and the suite stays fast (the gate counts the real inventory separately).
    """
    extra = (
        [f"--inventory={FIXTURES / 'mcp-tool-inventory.json'}"]
        if inventory
        else ["--no-inventory"]
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, *extra],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class TestTheSnapshotContract:
    def test_the_fixture_is_a_valid_snapshot(self):
        import jsonschema

        schema = json.loads((REPO / "contracts" / "turn-snapshot.schema.json").read_text("utf-8"))
        snapshot = json.loads((FIXTURES / "turn-snapshot-valid.json").read_text("utf-8"))
        jsonschema.validate(snapshot, schema)


class TestTheGoodControl:
    def test_it_is_accepted(self):
        result = run(str(FIXTURES / "worker-proposal-valid.json"), str(FIXTURES / "turn-snapshot-valid.json"))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VERDICT: ACCEPT" in result.stdout

    def test_a_unit_id_carried_only_in_the_tools_own_text_is_recognised(self):
        # The fixture cites 1376265, which appears in the snapshot only inside the unit's
        # `detail` string ("... [id:1376265, idx:9]"). Acceptance proves the checker reads it.
        result = run(str(FIXTURES / "worker-proposal-valid.json"), str(FIXTURES / "turn-snapshot-valid.json"))
        assert "not in the snapshot" not in result.stdout
        assert "2 known ids" in result.stdout


    def test_the_assessment_names_the_tactic_file(self):
        proposal = json.loads((FIXTURES / "worker-proposal-valid.json").read_text("utf-8"))
        assert proposal["assessment"].startswith("prompts/tactics/")


class TestTheNegativeControl:
    def test_every_kind_of_violation_is_reported(self):
        result = run(str(FIXTURES / "worker-proposal-invalid.json"), str(FIXTURES / "turn-snapshot-valid.json"))
        assert result.returncode == 1
        assert "VERDICT: REJECT" in result.stdout
        for expected in (
            "additional properties are not allowed",  # extra field the schema forbids
            "unknown tool 'attack_unit_now'",          # a tool that does not exist
            "no argument(s) ['nonsense_argument']",    # an argument that tool does not take
            "duplicate actionId bad-3",                # repeated id
            "unit 999999 is not in the snapshot",      # invented unit
        ):
            assert expected.lower() in result.stdout.lower(), f"missing: {expected}"

    def test_a_valid_proposal_is_not_rejected_by_the_same_run(self):
        # Guard against a checker that simply rejects everything.
        result = run(str(FIXTURES / "worker-proposal-valid.json"), str(FIXTURES / "turn-snapshot-valid.json"))
        assert "REJECT" not in result.stdout


class TestTheBriefAndValidatorAgreeOnVocabulary:
    def test_the_validator_is_the_phase_three_script_from_the_skill(self):
        skill = (REPO / ".dsh" / "skills" / "civ6-orchestrator" / "SKILL.md").read_text("utf-8")
        assert "Phase 3: Validate and synthesize" in skill
        assert SCRIPT.exists()

    @pytest.mark.parametrize(
        "tool",
        ["unit_action", "get_units", "city_action", "set_city_production"],
    )
    def test_the_fixture_tools_are_real_mcp_tools(self, tool):
        # The names the fixture uses must exist in the server's own tool list; the static gate
        # counts the inventory, this pins the handful the proposal contract depends on.
        server = (REPO / "src" / "civ_mcp" / "server.py").read_text("utf-8")
        assert f"def {tool}(" in server
