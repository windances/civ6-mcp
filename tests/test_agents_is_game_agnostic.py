"""`AGENTS.md` is injected into every session of every match in this checkout - keep it generic.

The reference is the one document the harness pastes into the system prompt, so everything in it is
paid for by every game, not only the one it was learned in. Mechanics, tells and costs transfer
between games; **this match's coordinates, city names, unit ids and live state do not**. The
2026-09-26 split moved task *status* out for the same reason; this keeps the *evidence* out.

The lesson is not deleted when it leaves the reference, it is relocated: the turn-by-turn record
lives in `docs/retrospectives/<date>-<subject>.md` and the retired task files in
`prompts/tasks/tmp/done/`, and the reference points at them. `tests/test_agents_references.py`
already proves those pointers resolve; this file proves the numbers they replace are gone - and that
they landed somewhere, so a rewrite cannot quietly lose the evidence.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
DIRECTIVE = ROOT / "prompts" / "strategies" / "china-conquest" / "directive.md"
RECORD = ROOT / "docs" / "retrospectives" / "2026-09-27-thebes-alexandria-T194-T218.md"

TEXT = AGENTS.read_text(encoding="utf-8-sig")

# A backticked token is a path or an identifier the reference is *supposed* to name; a path may
# legitimately be called `docs/retrospectives/2026-09-21-moscow-war-T101-T116.md`. Prose is what
# has to stay generic, so the checks below read the text with those tokens removed.
BACKTICKED = re.compile(r"`[^`]+`")


def prose(text: str) -> str:
    return BACKTICKED.sub(" ", text)


def prose_lines(text: str) -> list[str]:
    return [prose(line) for line in text.splitlines()]


UNIT_ID = re.compile(r"#\d{5,}")
TURN_REF = re.compile(r"\bT\d{2,4}\b")
COORD = re.compile(r"\((\d{1,3}),\s?(\d{1,3})\)")
NARRATIVE_TAIL = re.compile(r"\bthen \d")

# The Coordinate System's own teaching example is the one coordinate pair the reference may carry:
# it exists to define the axes, not to describe a match.
ALLOWED_COORDS = frozenset({"9,24", "9,26"})

# This match's cities. A new game has none of them, and a reader who has not played this one learns
# nothing from them.
MATCH_CITIES = (
    "Astrakhan", "Moscow", "Voronezh", "Kazan", "Novgorod", "Yerevan",
    "St Petersburg", "St. Petersburg", "Thebes", "Alexandria", "Heliopolis",
    "Memphis", "Abydos", "Amsterdam", "Sena",
)

# Phrasing that reads as *this* game's state or *this* strategy, rather than as the interface.
STRATEGY_VOICE = (
    "China buys",
    "Peace is not an option",
    "the directive's and is blunt",
)

# Evidence anchors are allowed, but they must be few and they must read as evidence ("measured"),
# not as state ("the army is at ..."). Four leaves room for a genuine cross-game case.
MAX_TURN_REFS = 4


class TestNoGameStateInTheReference:
    def test_no_unit_ids(self):
        found = UNIT_ID.findall(TEXT)
        assert not found, (
            "AGENTS.md carries unit ids, which are this match's state and are meaningless in the "
            f"next game: {found}. Put the ledger in a done/ task record or a retrospective."
        )

    def test_no_match_coordinates(self):
        found = {(x, y) for x, y in COORD.findall(TEXT)}
        stray = sorted(f"{x},{y}" for x, y in found if f"{x},{y}" not in ALLOWED_COORDS)
        assert not stray, (
            f"AGENTS.md carries tile coordinates: {stray}. Only the Coordinate System example "
            f"{sorted(ALLOWED_COORDS)} may stay."
        )

    def test_no_match_city_names_in_prose(self):
        offenders = [
            (number, name)
            for number, line in enumerate(prose_lines(TEXT), start=1)
            for name in MATCH_CITIES
            if name.lower() in line.lower()
        ]
        assert not offenders, (
            "AGENTS.md names a city from this match in prose: "
            + "; ".join(f"line {n}: {name}" for n, name in offenders)
            + ". The trap transfers; the city does not."
        )

    def test_no_live_state_claims(self):
        offenders = [
            (number, phrase)
            for number, line in enumerate(prose_lines(TEXT), start=1)
            for phrase in STRATEGY_VOICE
            if phrase.lower() in line.lower()
        ]
        assert not offenders, (
            "AGENTS.md states this game's strategy or situation as fact: "
            + "; ".join(f"line {n}: {phrase!r}" for n, phrase in offenders)
            + ". Attribute it to the directive and point at it instead."
        )


class TestEvidenceAnchorsStayAnchors:
    def test_turn_references_are_few(self):
        lines = [n for n, line in enumerate(prose_lines(TEXT), 1) if TURN_REF.search(line)]
        assert len(lines) <= MAX_TURN_REFS, (
            f"AGENTS.md cites {len(lines)} turns (limit {MAX_TURN_REFS}): lines {lines}. Each one is "
            "a fact only this match can use; keep the tell and move the story to a retrospective."
        )

    def test_every_turn_reference_reads_as_evidence(self):
        lines = prose_lines(TEXT)
        bare = [
            number
            for number, line in enumerate(lines, 1)
            if TURN_REF.search(line)
            and "measured" not in line.lower()
            and "measured" not in (lines[number - 2].lower() if number > 1 else "")
        ]
        assert not bare, (
            "a turn number appears without saying it is a measurement, so it reads as current "
            f"state: lines {bare}"
        )

    def test_no_narrative_tails(self):
        offenders = [
            (number, line.strip()[:80])
            for number, line in enumerate(prose_lines(TEXT), start=1)
            if NARRATIVE_TAIL.search(line)
        ]
        assert not offenders, (
            "a step-by-step narrative ('then 85, then 55') is a record, not an interface fact: "
            + "; ".join(f"line {n}: {text}" for n, text in offenders)
        )


class TestTheLessonLandedSomewhere:
    """Removing evidence is only allowed if it has a home - otherwise the next reader loses it."""

    def test_the_relocated_strategy_rules_are_in_the_directive(self):
        directive = DIRECTIVE.read_text(encoding="utf-8-sig")
        assert "No peace, ever" in directive, "the no-peace rule belongs to the directive"
        assert "Never buy a religious unit" in directive, (
            "the reference no longer states China's religious-unit policy, so the directive must"
        )

    def test_the_relocated_measurements_are_in_the_record(self):
        assert RECORD.is_file(), "the case record the reference points at must exist"
        record = RECORD.read_text(encoding="utf-8-sig")
        for needle in ("read unchanged", "Astrakhan", "NO_MOVES", "SIEGE PROGRESS"):
            assert needle in record, (
                f"the record must carry the evidence the reference dropped: {needle!r} is missing"
            )

    def test_the_old_phrasings_are_gone(self):
        for gone in ("T140-T142", "T65", "T83", "China buys no religious unit",
                     "Peace is not an option"):
            assert gone not in TEXT, f"AGENTS.md still carries {gone!r}"


class TestTheChecksAreNotVacuous:
    def test_the_denylists_are_populated(self):
        assert MATCH_CITIES and STRATEGY_VOICE and ALLOWED_COORDS
        assert MAX_TURN_REFS >= 1

    def test_prose_strips_real_tokens(self):
        # If AGENTS.md stopped using backticks this test's premise would vanish silently. A path may
        # name a match file - `docs/retrospectives/2026-09-27-...-T194-T218.md` - so the checks read
        # the text with backticked tokens removed, and this pins that they really are removed.
        assert prose(TEXT) != TEXT, "no backticked tokens were stripped"
        stripped = prose("`docs/retrospectives/x-T194-T218.md` Moscow")
        assert "Moscow" in stripped
        assert "docs/retrospectives" not in stripped and "T194" not in stripped

    def test_the_reference_is_the_document_we_think_it_is(self):
        assert len(TEXT) > 30_000, "AGENTS.md got suspiciously small"
        assert "Temporary tasks are files" in TEXT
        assert "Strategic Patterns" in TEXT
