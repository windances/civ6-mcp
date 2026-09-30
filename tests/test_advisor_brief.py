"""An advisor brief must paste the doctrine, and a paste is a copy that drifts.

The advisor holds no filesystem, so every rule it must obey is inside the message - which makes the
brief the only place a tactic file reaches an advisor, and a hand-made paste the only thing standing
between the file and the advisor. **Measured 2026-09-30**: the rehearsal brief at
`.tools/_advisor-brief.md` pastes a revision of `tactics/02` and `tactics/05` that is **missing one
whole section of each** - `## If the contact happens while the army is still assembling` and
`## The end-of-turn warning that enforces the first of those` - and both are sections added *after* the
paste was taken. The doctrine an advisor never sees is the doctrine that is newest.

`scripts/advisor-brief.py` reads the doctrine from disk, and this file holds it to three things: the
paste is byte-identical to the file, the digest it prints is the file's digest today, and every heading
of the source survives.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("advisor_brief", ROOT / "scripts" / "advisor-brief.py")
assert _spec and _spec.loader
brief_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(brief_tool)

# The four files this check was written for: the assault's analysis, staging, formation and fire.
THE_ASSAULT = ["04", "05", "06", "07"]


def generated() -> str:
    return brief_tool.build_brief(THE_ASSAULT, role="military-map")


def test_the_pasted_doctrine_is_the_file_byte_for_byte():
    problems = brief_tool.verify_brief(generated(), root=ROOT)
    assert problems == [], problems


def test_the_four_assault_files_really_are_the_ones_pasted():
    text = generated()
    for spec in THE_ASSAULT:
        path = brief_tool.resolve_tactic(spec)
        assert path.relative_to(ROOT).as_posix() in text, f"{spec} was not pasted"


def test_the_fence_survives_a_file_that_contains_fences():
    """These files fence their own examples, so a fixed ``` would end the paste early."""
    for spec in THE_ASSAULT:
        path = brief_tool.resolve_tactic(spec)
        body = brief_tool.read(path)
        fence = brief_tool.fence_for(body)
        longest = max(len(m.group(0)) for m in __import__("re").finditer(r"`+", body))
        assert len(fence) > longest, f"{path.name}: a {len(fence)}-backtick fence holds {longest}"


def test_a_bare_number_resolves_with_or_without_its_leading_zero():
    """PowerShell coerces `--tactics 04,05` to `4`, `5`, so `4` must resolve to `04`."""
    assert brief_tool.resolve_tactic("7") == brief_tool.resolve_tactic("07")
    assert brief_tool.resolve_tactic("4") == brief_tool.resolve_tactic("04")
    assert brief_tool.resolve_tactic("04").name == "04-staging-out-of-range.md"
    assert brief_tool.resolve_tactic("07-pre-war-analysis") == brief_tool.resolve_tactic("07")


def test_an_unknown_tactic_names_what_exists():
    with pytest.raises(SystemExit) as raised:
        brief_tool.resolve_tactic("99-not-a-file")
    assert "07-pre-war-analysis" in str(raised.value), "the refusal must list the real files"


def test_the_checker_names_a_trimmed_paste_by_its_missing_section():
    """The failure this exists for: a paste that quietly lacks a heading the file has."""
    text = generated()
    source = brief_tool.read(brief_tool.resolve_tactic("05"))
    missing = brief_tool.headings(source)[-1]
    trimmed = "\n".join(line for line in text.splitlines() if line != missing)
    assert trimmed != text, "the fixture heading was not in the brief"
    problems = brief_tool.verify_brief(trimmed, root=ROOT)
    assert any("missing a whole section" in problem for problem in problems), problems


def test_a_hand_made_unfenced_paste_is_audited_too():
    """The briefs this check exists for paste unfenced, straight after the heading.

    A brief that cannot even say which revision it pasted is the one worth auditing, so both shapes
    are read - and the report for the repo's own rehearsal brief names exactly the two sections the
    independent measurement found.
    """
    source = brief_tool.read(brief_tool.resolve_tactic("07"))
    kept = "\n".join(line for line in source.splitlines() if not line.startswith("## "))
    legacy = f"#### prompts/tactics/07-pre-war-analysis.md\n{kept}\n"
    problems = brief_tool.verify_brief(legacy, root=ROOT)
    joined = "\n".join(problems)
    assert "carries no sha256" in joined
    assert "the pasted text is not the file" in joined
    assert "missing a whole section" in joined


def test_a_brief_that_pastes_nothing_is_not_called_clean():
    problems = brief_tool.verify_brief("# A brief with no doctrine in it\n", root=ROOT)
    assert problems == ["no doctrine section found: a brief that pastes nothing cannot be checked"]
