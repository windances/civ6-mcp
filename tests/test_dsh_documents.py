"""The documents DSH serves the model are English, and the Chinese backups beside them are inert.

Human instruction 2026-09-28, extending 2026-09-27's `AGENT.md全用英文`: every `.md` file DSH hands
the model is English and pure ASCII - **a change that arrives in Chinese is translated into English and
written to the English file** - and each one has a Chinese **backup** `<name>.cn.md` beside it, which
is generated *from* the English for a human reader. The backup is never a source: nothing writes to it,
no code path reads it, and DSH cannot load it.

Measured 2026-09-28, DSH serves exactly three kinds of document in this workspace, and each was read
off the harness source rather than assumed:

| Document | Reaches the model through | Evidence |
|---|---|---|
| `AGENTS.md` | the harness, once per session | `deepseek-harness/packages/context/agent-instructions/src/config.ts`: `DEFAULT_INSTRUCTION_FILE_CANDIDATES = ['AGENTS.md', 'CLAUDE.md']` |
| `.dsh/skills/civ6-orchestrator/SKILL.md` | the `skill` tool | `packages/skill/skill-filesystem/src/index.ts`: for a directory under a skill root the entry must be exactly `SKILL.md` (`segments[1] === 'SKILL.md'`) |
| `prompts/strategies/<name>/directive.md` | nothing directly - it is copied *into* that skill by `scripts/use-strategy.ps1` | the block invariant in `tests/test_strategy_block.py` |

So a backup is unreachable in two independent ways: no instruction candidate ends in `.cn.md`, and a
skill has to be a file named exactly `SKILL.md`. The one shape that *would* load is a `.md` file
sitting directly in a skill root - `discoverRoot` takes any `*.md` entry there as a skill - which is
what `test_a_backup_is_not_parked_in_a_skill_root` keeps from happening.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import text_encoding  # noqa: E402

AGENTS = ROOT / "AGENTS.md"
SKILL = ROOT / ".dsh" / "skills" / "civ6-orchestrator" / "SKILL.md"
PRESETS = ROOT / "prompts" / "strategies"
BACKUP_SUFFIX = ".cn.md"

# The harness's own loader vocabulary, quoted above. A file named one of these would be injected as
# workspace instructions, or loaded as the skill, in place of the English file it backs up.
INSTRUCTION_CANDIDATES = ("AGENTS.md", "CLAUDE.md", "AGENTS.local.md", "CLAUDE.local.md")
SKILL_FILE_NAME = "SKILL.md"

# Every code path that reads or writes a served document. A backup must appear in none of them.
READERS_AND_WRITERS = (
    "scripts/use-strategy.ps1",
    "scripts/use-strategy.sh",
    "scripts/set-strategy.ps1",
    "scripts/set-strategy.sh",
    "src/civ_mcp/strategy_directive.py",
)


def served_documents() -> list[pathlib.Path]:
    """Every document DSH can put in front of the model, in the order the table above lists them."""
    return [AGENTS, SKILL, *sorted(PRESETS.glob("*/directive.md"))]


def backup_of(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.name[: -len(".md")] + BACKUP_SUFFIX)


def backups() -> list[pathlib.Path]:
    return [backup_of(path) for path in served_documents()]


def cjk_characters(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def without_fences(text: str) -> str:
    """The document with its fenced code blocks removed.

    A fence line carries three backticks, not one, so any span-by-span reading that keeps the fences
    shifts its pairing from there on and starts inventing "spans" out of English prose. The fenced
    blocks themselves are byte-identical in a faithful translation and are checked by reading the
    backup, so they are dropped here rather than tokenised.
    """
    kept: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def inline_spans(text: str) -> list[str]:
    """Every inline ``code span`` in `text`, whitespace-normalised, in order and without repeats.

    A span the source wraps across two lines has its backticks on different lines, so a per-line regex
    pairs the wrong ones; here a line break *inside* a span is read as a space, and both the span and
    the backup it is looked up in are whitespace-collapsed, so a wrapped span still matches its
    verbatim copy. An unterminated final span is dropped rather than reported.
    """
    spans: list[str] = []
    current: list[str] = []
    inside = False
    for char in text:
        if char == "`":
            if inside:
                spans.append(" ".join("".join(current).split()))
                current = []
            inside = not inside
        elif inside:
            current.append(" " if char == "\n" else char)
    return [span for span in dict.fromkeys(spans) if span]


class TestTheServedDocumentsAreEnglish:
    def test_the_set_is_what_the_harness_reads(self):
        found = served_documents()
        assert all(path.is_file() for path in found), [str(p) for p in found if not p.is_file()]
        # One reference, one skill, one directive per preset: each is a document DSH can serve.
        assert AGENTS in found and SKILL in found
        assert len([p for p in found if p.name == "directive.md"]) == len(list(PRESETS.glob("*/directive.md")))
        assert len(found) >= 3, f"the served set collapsed to {found}"

    def test_each_one_is_pure_ascii_with_no_bom(self):
        for path in served_documents():
            raw = path.read_bytes()
            assert not raw.startswith(text_encoding.BOM), (
                f"{path.relative_to(ROOT)} is English, so it must carry no BOM - run "
                "`python scripts/fix-text-encoding.py`"
            )
            bad = [
                (number, line)
                for number, line in enumerate(raw.decode("utf-8").splitlines(), start=1)
                if not line.isascii()
            ]
            assert not bad, (
                f"{path.relative_to(ROOT)} is English only, so it must be pure ASCII (human instruction "
                "2026-09-28): translate the line into English and write the English. Run "
                "`python scripts/fix-text-encoding.py` to normalise the marks first: "
                + "; ".join(f"line {number}: {line.strip()[:60]}" for number, line in bad[:3])
            )

    def test_the_gate_holds_the_same_set(self):
        # The enforcement is `ASCII_ONLY`, matched on the file *name*; this test is the reader-facing
        # half. If a name here stops being in that tuple the gate silently stops covering it.
        covered = set(text_encoding.ASCII_ONLY)
        missing = sorted({path.name for path in served_documents()} - covered)
        assert not missing, (
            f"{missing} is served to the model but not held to the English bar by "
            f"text_encoding.ASCII_ONLY ({sorted(covered)})"
        )
        assert text_encoding.ascii_lines(ROOT) == [], (
            "the module the pre-commit hook runs disagrees with this test about a non-ASCII line"
        )
        assert text_encoding.stray_boms(ROOT) == []


class TestTheBilingualDocuments:
    """The one exception to the English bar, pinned so it cannot be mistaken for drift.

    Human instruction 2026-09-30: 用于中英对照的文档除外 - a document written to be read side by side
    is not held to the English-only bar. That is the per-decision playbooks under `prompts/tactics/`:
    a bilingual H1, the human's own instructions quoted verbatim in Chinese, and the prose in English
    so the rule can be followed from either side.

    Both mistakes are one edit away, which is why this is a test rather than a comment. Translating
    the quotes away loses the instruction a rule came from (the directive quotes them for the same
    reason); adding a playbook to `text_encoding.ASCII_ONLY` - which matches on file *name* - would
    fail the gate on a document that is correct, and the pressure to "fix" it would land on the
    Chinese the human asked to keep.
    """

    TACTICS = ROOT / "prompts" / "tactics"

    def playbooks(self) -> list[pathlib.Path]:
        return sorted(p for p in self.TACTICS.glob("*.md") if p.name != "README.md")

    def test_the_exception_set_is_the_per_decision_playbooks(self):
        found = self.playbooks()
        assert len(found) >= 8, f"the playbook set collapsed to {[p.name for p in found]}"

    def test_none_of_them_is_held_to_the_pure_ascii_bar(self):
        for path in self.playbooks():
            assert path.name not in text_encoding.ASCII_ONLY, (
                f"{path.name} is bilingual by design; adding it to text_encoding.ASCII_ONLY would "
                "make the gate fail on a correct document"
            )
            assert path not in served_documents(), (
                f"{path.relative_to(ROOT)} would then be served to the model as English"
            )

    def test_each_one_opens_with_a_bilingual_title(self):
        for path in self.playbooks():
            head = path.read_text(encoding="utf-8-sig").splitlines()[0]
            assert " / " in head and cjk_characters(head) > 0, (
                f"{path.relative_to(ROOT)} opens with {head[:80]!r} - a bilingual document's title "
                "carries both languages, which is what marks it as the exception"
            )

    def test_each_one_still_carries_a_bom_and_real_chinese(self):
        # The exception is to the English-only bar, not to the BOM rule: these files hold CJK.
        for path in self.playbooks():
            assert path.read_bytes().startswith(text_encoding.BOM), (
                f"{path.relative_to(ROOT)} holds Chinese and must carry a BOM"
            )
            assert cjk_characters(path.read_text(encoding="utf-8-sig")) > 0, (
                f"{path.relative_to(ROOT)} has no Chinese left - if the quotes were translated away, "
                "say so in the diary and in the file, and do not leave it in the bilingual set"
            )


class TestTheChineseBackups:
    def test_every_served_document_has_a_backup(self):
        missing = [str(b.relative_to(ROOT)) for b in backups() if not b.is_file()]
        assert not missing, (
            "every document the model reads has a Chinese backup beside it (human instruction "
            f"2026-09-28); these are missing: {missing}"
        )

    def test_a_backup_holds_chinese_and_is_not_a_stub(self):
        for path, backup in zip(served_documents(), backups(), strict=True):
            text = backup.read_text(encoding="utf-8")
            source_lines = len(path.read_text(encoding="utf-8").splitlines())
            # A complete translation carries Chinese on most of the source's lines, so the floor is
            # per source line rather than a flat number: `balanced/directive.md` is two lines long.
            floor = max(20, source_lines * 5)
            assert cjk_characters(text) >= floor, (
                f"{backup.relative_to(ROOT)} holds {cjk_characters(text)} CJK characters, under the "
                f"{floor} a translation of {path.name} ({source_lines} lines) should carry - it is a "
                "stub, not a translation"
            )
            # Chinese is more compact than English, so the bar is a third of the source's bytes.
            assert len(text.encode("utf-8")) >= len(path.read_bytes()) // 3, (
                f"{backup.relative_to(ROOT)} is much shorter than {path.name} - check that it is the "
                "whole document, not a summary"
            )

    def test_a_backup_covers_every_identifier_the_english_document_names(self):
        """A backup is generated, so it drifts silently - and nothing else here notices.

        Measured 2026-09-28: `AGENTS.cn.md` was nineteen hours and three English edits behind - a whole
        bullet (`python scripts/temp-task.py add ...`, which is how a task is filed) and a rewritten
        paragraph were missing from it - while every other check in this class stayed green, because
        "holds Chinese", "is not a stub" and "says it is a backup" are all true of a stale translation.

        The check is coverage, not wording: a path, command, flag, tool name or metric id is never
        translated, so every inline span of the English document has to appear somewhere in its backup.
        The `IN FORCE NOW` line is exempt - it is match state, rewritten every time a task is added or
        retired, and the session filing a task does not owe the backup a retranslation of that line.
        Measured with this tokenizer: AGENTS 279 spans / SKILL 127 / china-conquest directive 66, none
        missing; the fence-blind version of the same check reported 260 and 11 "misses" that were all
        artifacts of a fence line's third backtick.
        """
        for path, backup in zip(served_documents(), backups(), strict=True):
            english = without_fences(path.read_text(encoding="utf-8"))
            english = "\n".join(
                line for line in english.splitlines() if "IN FORCE NOW" not in line
            )
            haystack = " ".join(backup.read_text(encoding="utf-8-sig").split())
            missing = [span for span in inline_spans(english) if span not in haystack]
            assert not missing, (
                f"{backup.relative_to(ROOT)} does not carry these spans of {path.name}, so it was "
                f"translated from an older revision: {missing[:8]}"
                + (f" (and {len(missing) - 8} more)" if len(missing) > 8 else "")
                + ". Re-translate the file from the current English one."
            )

    def test_a_backup_says_that_it_is_a_backup(self):
        # The banner is what stops the next reader from editing the translation instead of the source.
        for path, backup in zip(served_documents(), backups(), strict=True):
            head = "\n".join(backup.read_text(encoding="utf-8-sig").splitlines()[:5])
            assert "备份" in head and path.name in head, (
                f"{backup.relative_to(ROOT)} does not say it is a backup of {path.name}; its first "
                f"lines are: {head[:160]!r}"
            )

    def test_a_backup_is_unambiguous_in_a_zh_cn_viewer(self):
        for backup in backups():
            assert backup.read_bytes().startswith(text_encoding.BOM), (
                f"{backup.relative_to(ROOT)} holds Chinese and must carry a BOM - run "
                "`python scripts/fix-text-encoding.py`"
            )
            assert not text_encoding.needs_bom(backup), "the BOM is missing"

    def test_a_backup_name_is_never_a_name_dsh_looks_for(self):
        for backup in backups():
            assert backup.name not in INSTRUCTION_CANDIDATES, (
                f"{backup.name} would be injected as workspace instructions"
            )
            assert backup.name != SKILL_FILE_NAME, f"{backup.name} would be loaded as the skill"

    def test_a_backup_is_not_parked_in_a_skill_root(self):
        # `discoverRoot` treats any `*.md` entry directly in a skill root as a skill, so a backup
        # dropped into `.dsh/skills/` itself would be served. It belongs beside the file it backs up.
        for backup in backups():
            parts = backup.relative_to(ROOT).parts
            if "skills" in parts:
                index = parts.index("skills")
                assert len(parts) > index + 2, (
                    f"{backup.relative_to(ROOT)} sits directly in a skill root, where DSH loads any "
                    "*.md file as a skill"
                )

    def test_no_code_path_reads_or_writes_a_backup(self):
        # The direction of the rule, checked where it can break: nothing that produces or delivers a
        # strategy may name a `.cn.md` file, so a backup can never become the live source. Comments may
        # mention the convention - a comment is not a path.
        for name in READERS_AND_WRITERS:
            source = (ROOT / name).read_text(encoding="utf-8-sig")
            code = "\n".join(
                line for line in source.splitlines() if not line.lstrip().startswith("#")
            )
            assert BACKUP_SUFFIX not in code, (
                f"{name} names a {BACKUP_SUFFIX} file; a backup is generated from the English document "
                "and is never read or written by the tooling"
            )

    def test_the_knowledge_index_ignores_a_backup(self):
        # The corpus walks `prompts/`, so a `directive.cn.md` would be indexed beside the English
        # directive it translates and `search_knowledge` would cite the translation.
        from civ_mcp import knowledge

        indexed = knowledge.iter_files([ROOT / "prompts", ROOT / "docs"])
        assert indexed, "the corpus walk found nothing - this test would pass vacuously"
        offenders = sorted(str(p.relative_to(ROOT)) for p in indexed if p.name.endswith(BACKUP_SUFFIX))
        assert not offenders, f"the index would serve a Chinese backup: {offenders}"
