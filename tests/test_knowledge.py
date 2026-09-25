"""The knowledge base: an agent has to be able to look a mechanic up mid-turn.

The gap this closes: the game manual is 557 KB of text, the directive and rule file are another
few hundred, and a turn cannot read them - but it does need them. `search_knowledge` answers with
the source path and line range of the matching passage, so the agent reads (and cites) the exact
lines instead of paraphrasing from memory.

Only the pieces that can be wrong on their own are tested here: chunking and line numbers,
ranking, the doc filter, the CJK fallback (`unicode61` does not split Chinese into words and this
SQLite build has no `trigram` tokenizer), the missing-index message, and the tool's formatting.
"""

from __future__ import annotations

import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import knowledge  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]


def scratch() -> pathlib.Path:
    """A scratch directory under .tools/ - the sandbox only lets tests write there."""
    path = REPO / ".tools" / f"_kb_env_{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


MANUAL_LIKE = """\
71

COMBAT

WHICH UNITS CAN FIGHT Any military unit may attack an enemy unit. Support units, such as the
Battering Ram or the Siege Tower cannot initiate attacks, but they help other units they are
grouped with.

HEALING DAMAGE TO CITIES A city heals a small amount every turn, even during combat, as long as
it has a supply line. A supply line is any hex adjacent to the city that is not within an enemy
unit's Zone of Control.

87

ZONES OF CONTROL Combat units exert a "zone of control" over the tiles around them. When a unit
moves into a tile within an enemy's ZOC it expends all of its MPs.
"""

TACTICS_LIKE = """\
# 6. Assault composition and fire discipline / 攻城开始后，部队搭配和攻击策略

## Order of work, every turn

1. Siege knocks the walls to 0.
2. Melee takes the city - 攻城时必须由近战单位进入城市格。

## Fire discipline

- Concentrate. Every attacker on the same target, in the same turn.
"""


class Fixture:
    """A tiny corpus + a private index, built once per test class use."""

    def __init__(self):
        self.root = scratch()
        (self.root / "manual.txt").write_text(MANUAL_LIKE, encoding="utf-8")
        (self.root / "tactics").mkdir(exist_ok=True)
        (self.root / "tactics" / "06-assault.md").write_text(TACTICS_LIKE, encoding="utf-8")
        self.db = self.root / "knowledge.sqlite"
        self.summary = knowledge.build([str(self.root)], db=self.db)


class TestChunking:
    def test_line_numbers_point_at_the_source(self):
        text = "line one\nline two\nline three\n"
        chunks = knowledge.chunk_text(text)
        assert len(chunks) == 1
        start, end, _section, body = chunks[0]
        assert (start, end) == (1, 3)
        assert "line two" in body

    def test_page_numbers_and_caps_titles_become_the_section(self):
        sections = [section for _s, _e, section, _b in knowledge.chunk_text(MANUAL_LIKE)]
        assert any(section.startswith("p") for section in sections), sections
        titled = knowledge.chunk_text("ZONES OF CONTROL\nCombat units exert a zone of control.\n")
        assert titled[0][2] == "ZONES OF CONTROL"

    def test_a_long_document_is_split_into_several_chunks(self):
        chunks = knowledge.chunk_text("para\n\n" * 400)
        assert len(chunks) > 1
        assert all(end >= start for start, end, _s, _b in chunks)


class TestIndexAndSearch:
    def test_it_finds_a_passage_and_cites_it(self):
        fix = Fixture()
        hits = knowledge.search("supply line city heals", db=fix.db)
        assert hits, "the healing rule is in the corpus"
        top = hits[0]
        assert top.doc.endswith("manual.txt")
        assert top.start_line <= top.end_line
        # snippet() wraps each matched term in brackets, so compare words, not phrases.
        lowered = top.snippet.lower()
        assert "supply" in lowered and "line" in lowered
        source = fix.root / "manual.txt"
        lines = source.read_text(encoding="utf-8-sig").splitlines()
        extracted = "\n".join(lines[top.start_line - 1 : top.end_line])
        assert "heals a small amount" in extracted, "the cited range must contain the passage"

    def test_ranking_puts_the_multi_term_match_first(self):
        fix = Fixture()
        hits = knowledge.search("battering ram cannot initiate attacks", db=fix.db)
        assert hits
        assert "battering" in hits[0].snippet.lower() and "ram" in hits[0].snippet.lower()

    def test_the_doc_filter_narrows_the_search(self):
        fix = Fixture()
        only_tactics = knowledge.search("city", k=5, doc="tactics/", db=fix.db)
        assert only_tactics
        assert all("tactics/" in hit.doc for hit in only_tactics)

    def test_a_chinese_query_finds_chinese_text(self):
        fix = Fixture()
        hits = knowledge.search("近战单位进入城市格", db=fix.db)
        assert hits, "the CJK fallback has to work: no trigram tokenizer in this sqlite build"
        assert any("近战" in hit.snippet for hit in hits)

    def test_an_unknown_query_returns_nothing_rather_than_raising(self):
        fix = Fixture()
        assert knowledge.search("zzz-nonexistent-token-zzz", db=fix.db) == []

    def test_a_missing_index_is_a_message_not_a_crash(self):
        missing = scratch() / "nothing.sqlite"
        assert knowledge.search("anything", db=missing) == []
        assert "kb.py index" in knowledge.build_hint()
        # With no index at all, the agent is told how to build one...
        assert "not found" in knowledge.format_hits([], "anything", db=missing)
        # ...and with an index that simply did not match, it is not sent to build anything.
        fix = Fixture()
        text = knowledge.format_hits([], "quantum catapults", db=fix.db)
        assert "kb.py index" not in text and "try fewer or different words" in text

    def test_stats_reports_what_is_indexed(self):
        fix = Fixture()
        info = knowledge.stats(db=fix.db)
        assert info["exists"] and info["chunks"] >= 2
        assert any(doc.endswith("manual.txt") for doc, _ in info["top"])


class TestTheToolAnswer:
    def test_every_hit_carries_source_lines_and_a_snippet(self):
        fix = Fixture()
        hits = knowledge.search("zone of control", db=fix.db)
        text = knowledge.format_hits(hits, "zone of control")
        assert text.startswith("KNOWLEDGE:")
        assert "manual.txt:" in text
        assert "[p" in text or "[" in text
        assert "read the source lines" in text

    def test_no_hits_still_tells_the_agent_what_to_do(self):
        missing = scratch() / "absent.sqlite"
        text = knowledge.format_hits([], "quantum catapults", db=missing)
        assert "No knowledge-base match" in text
        assert "kb.py index" in text


class TestTheShippedCorpus:
    """The index the agent actually queries should cover the doctrine, not only the manual."""

    def test_the_default_sources_are_the_doctrine_files(self):
        assert "prompts" in knowledge.DEFAULT_SOURCES
        assert "AGENTS.md" in knowledge.DEFAULT_SOURCES
        for source in knowledge.DEFAULT_SOURCES:
            if source != "docs":  # docs/ is optional in a fresh checkout
                assert (REPO / source).exists(), f"{source} should exist to be indexable"

    def test_iter_files_skips_ignored_directories(self):
        files = {str(path) for path in knowledge.iter_files([str(REPO / "prompts")])}
        assert files, "the shipped prompts should be indexable"
        assert not any("__pycache__" in path for path in files)
