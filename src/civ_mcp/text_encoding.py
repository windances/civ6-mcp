"""Which text files must carry a UTF-8 BOM, and the one command that puts it back.

A BOM-less UTF-8 file on a Chinese Windows machine is decoded as codepage 936 (GBK) by any editor
that cannot detect the encoding: `游戏应当已经在运行` renders as `娓告垙搴斿綋宸茬粡鍦ㄨ繍琛`. The bytes
are valid UTF-8 and nothing is corrupt - the viewer guessed and guessed wrong. Measured on this repo
on 2026-09-26 for a `.zh.txt` task file, an English one (twelve em dashes), `AGENTS.md`, and the
strategy/tactics documents.

The policy is one line per family: a document holding a non-ASCII byte carries a BOM, an English
`.en.` file is pure ASCII and carries none, and a Chinese `.zh.` file always carries one. **`AGENTS.md`
is held to the English bar too** (human instruction 2026-09-27: AGENT.md全用英文): every session reads
it, so it is pure ASCII with no BOM, and a non-ASCII character in it is either a translation somebody
started and did not finish or a typographic mark - `ascii_lines` finds the first, `ascii_fix`
normalises the second.

**The writers are the weak point.** The agent's own file tools (`write`/`edit` in the harness) emit
plain UTF-8 with no BOM, so editing any of these documents silently strips it - measured twice, on
`prompts/tasks/continue-current.zh.txt` and on `AGENTS.md`. Nothing in this module can change that;
what it does is make the loss visible (`offenders`) and repair it in one command:

    python scripts/fix-text-encoding.py          # put the BOM back, report what changed
    python scripts/fix-text-encoding.py --check  # report only, exit 1 when something is missing
"""

from __future__ import annotations

import pathlib

BOM = b"\xef\xbb\xbf"
DOC_SUFFIXES = frozenset({".md", ".txt"})

# Runtime and derived trees: not part of the readable corpus, and written by tools that have no
# business carrying a display hint (JSON state, save files, caches, leaked temp envs).
SKIP_PARTS = frozenset(
    {
        ".git",
        ".dsh-home",
        ".civ6-mcp-data",
        ".tmp",
        ".tools",
        ".uv-cache",
        ".venv",
        ".pytest_cache",
        ".pytest-tmp",
        "__pycache__",
        "node_modules",
        "saves",
        "eval-logs",
        "mission-control",
    }
)


def documents(root: str | pathlib.Path) -> list[pathlib.Path]:
    """Every ``*.md`` / ``*.txt`` under ``root`` that a human could open, in a stable order."""
    base = pathlib.Path(root)
    found = []
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in DOC_SUFFIXES:
            continue
        parts = path.relative_to(base).parts
        if any(part in SKIP_PARTS or part.startswith("_kb_env_") for part in parts):
            continue
        found.append(path)
    return sorted(found)


def needs_bom(path: str | pathlib.Path) -> bool:
    """True when this document holds a non-ASCII byte and does not start with a BOM."""
    raw = pathlib.Path(path).read_bytes()
    if raw.startswith(BOM):
        return False
    return any(byte > 127 for byte in raw)


def offenders(root: str | pathlib.Path) -> list[pathlib.Path]:
    """The documents that would show as mojibake in a GBK viewer."""
    return [path for path in documents(root) if needs_bom(path)]


def fix(root: str | pathlib.Path) -> list[pathlib.Path]:
    """Write the BOM back onto every offender. Returns the files that were changed."""
    fixed = []
    for path in offenders(root):
        text = path.read_text(encoding="utf-8")  # BOM-less here by definition
        path.write_bytes(BOM + text.encode("utf-8"))
        fixed.append(path)
    return fixed


# --------------------------------------------------------------------------------------
# Content integrity: a BOM says nothing about whether the text inside is still the text
# --------------------------------------------------------------------------------------
#
# Measured 2026-09-26: a `Get-Content | Set-Content` round trip had decoded five files as GBK and
# re-encoded them as UTF-8, so `在集结前` became `鍦ㄩ泦缁撳墠` and every em dash became `鈥?`. The bytes
# were valid UTF-8 and the BOMs were in place, so `offenders()` was silent and 843 tests passed. These
# lines were in source files, docstrings and `SETUP-WINDOWS.md` - including the game's own menu
# labels - so a rule that cannot see this is a rule that misses the failure that actually happened.

SOURCE_SUFFIXES = frozenset({".py", ".md", ".txt", ".lua", ".ps1"})

# Characters that arriving through the GBK round trip is the signature of the damage. A line carrying
# three of them is not Chinese prose; the true positives measured on this repo carried dozens.
_MOJIBAKE_MARKERS = frozenset(
    "锛鐨娴鍦閿閸缁鏄銆鐢鍑涓鏂鍚鎴鎾鏌浜浣鍙閫鏃绋搴骞鍘鐜閭濮鎵鐩镐綅鑳芥垜浠粬璇村ソ"
)

# A line that *discusses* the artefact shows it on purpose: the recovery notes in `docs/`, the
# docstring in this module, `SETUP-WINDOWS.md`'s "the prefix is missing" example, and the loyalty
# test's U+FFFD sample. A checker that cannot tell an example from an accident is one somebody
# switches off, so the mention of the artefact is the exemption.
_SELF_REFERENTIAL = ("mojibake", "u+fffd", "prefix is missing", "gbk", "codepage 936")


def source_files(root: str | pathlib.Path) -> list[pathlib.Path]:
    """Every file a reader is expected to read as text, source included, in a stable order."""
    base = pathlib.Path(root)
    found = []
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        parts = path.relative_to(base).parts
        if any(part in SKIP_PARTS or part.startswith("_kb_env_") for part in parts):
            continue
        found.append(path)
    return sorted(found)


def looks_corrupt(line: str) -> bool:
    """One line, judged on its own: the four shapes the GBK round trip leaves behind."""
    if any(0xE000 <= ord(ch) <= 0xF8FF or ch == "\ufffd" for ch in line):
        return True
    if any(ch == "?" and i and ord(line[i - 1]) > 0x7F for i, ch in enumerate(line)):
        return True
    return sum(1 for ch in line if ch in _MOJIBAKE_MARKERS) >= 3


def self_referential(lines: list[str]) -> set[int]:
    """Indices of lines a checker must not judge: the artefact's own documentation and examples.

    A line is exempt when the file *is talking about* the damage within five lines of it - the
    recovery notes, this module's docstring, `SETUP-WINDOWS.md`'s "the prefix is missing" example,
    the retrospective that quotes a mangled advice string, the loyalty test's U+FFFD sample - and
    the marker table is exempt because those characters are its data. A checker that cannot tell an
    example from an accident is one somebody switches off.
    """
    notes = {
        i for i, line in enumerate(lines) if any(word in line.lower() for word in _SELF_REFERENTIAL)
    }
    exempt = set(notes)
    for i in notes:
        exempt.update(range(max(0, i - 5), min(len(lines), i + 6)))
    exempt.update(i for i, line in enumerate(lines) if "_MOJIBAKE_MARKERS" in line)
    return exempt


def corrupt_lines(root: str | pathlib.Path) -> list[tuple[pathlib.Path, int, str]]:
    """(path, line number, text) for every line that still carries the GBK round trip's damage."""
    found = []
    for path in source_files(root):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        exempt = self_referential(lines)
        for i, line in enumerate(lines):
            if i in exempt:
                continue
            if looks_corrupt(line):
                found.append((path, i + 1, line.strip()))
    return found


# --------------------------------------------------------------------------------------
# English only: every document DSH serves the model is pure ASCII
# --------------------------------------------------------------------------------------
#
# Human instruction 2026-09-27 (AGENT.md全用英文), extended 2026-09-28 to every document DSH hands
# the model: the agent reference is English, and English here means the bar the `.en.` files are
# already held to - **pure ASCII**, the one encoding no viewer can guess wrong. Two kinds of
# non-ASCII turn up in practice, and they need different treatment: the typographic marks
# (`—`, `→`, `…`, `≤`) are a mechanical substitution, and CJK prose is a sentence somebody has to
# write in English. `ascii_fix` does the first, `ascii_lines` reports the second, and the pre-commit
# hook runs both, so the file cannot drift back into a half-translated state.
#
# The three names below are matched on `path.name`, and each is a file DSH actually reads:
#
# * `AGENTS.md` - injected by the harness every session (deepseek-harness,
#   `packages/context/agent-instructions/src/config.ts`: the candidates are `AGENTS.md`/`CLAUDE.md`).
# * `SKILL.md` - the orchestrator skill, served by the `skill` tool. The loader requires exactly this
#   file name in a skill directory (`packages/skill/skill-filesystem/src/index.ts`, `segments[1] ===
#   'SKILL.md'`), which is also why a Chinese mirror can never be loaded - see `test_dsh_documents`.
# * `directive.md` - `scripts/use-strategy.ps1` copies one into the DIRECTIVE block of `SKILL.md`, so
#   a preset holding Chinese re-injects it on the next switch: it is the same defect one step earlier.
#
# The English file is the source: a change that arrives in Chinese is translated into English and
# written there (human instruction 2026-09-28). `scripts/set-strategy.*` refuses non-ASCII text for the
# same reason. Each file has a Chinese **backup** beside it, `<name>.cn.md`, generated from the English
# for a human reader, never edited and never a source - and no DSH search pattern matches it.
#
# **The deliberate exception: documents written to be read side by side** (human instruction
# 2026-09-30, 用于中英对照的文档除外). The per-decision playbooks under `prompts/tactics/` carry a
# bilingual H1 and quote the human's own instructions verbatim in Chinese; the `.zh.`/`.en.` prompt
# pairs are two files of one instruction. Those are correct as they are, so they are **not** in this
# tuple - the bar is matched on `path.name`, so no tactics file is ever held to pure ASCII. They still
# carry a BOM, because they hold non-ASCII bytes and that rule has no exception.
ASCII_ONLY = ("AGENTS.md", "SKILL.md", "directive.md")

# Applied to ASCII-only documents by `ascii_fix`, longest mark first so `—` never eats a `–`.
ASCII_MARKS = (
    ("\u2014", " - "),   # em dash
    ("\u2013", "-"),     # en dash
    ("\u2192", "->"),    # right arrow
    ("\u2026", "..."),   # horizontal ellipsis
    ("\u2264", "<="),    # less-or-equal
    ("\u2265", ">="),    # greater-or-equal
    ("\u00d7", "x"),     # multiplication sign
    ("\u00a0", " "),     # no-break space
    ("\u2018", "'"),     # curly quotes, all four, because a document is not a word processor
    ("\u2019", "'"),
    ("\u201c", '"'),
    ("\u201d", '"'),
)


def ascii_only_documents(root: str | pathlib.Path) -> list[pathlib.Path]:
    """The documents held to the pure-ASCII bar, that are present in this tree."""
    return [path for path in documents(root) if path.name in ASCII_ONLY]


def ascii_lines(root: str | pathlib.Path) -> list[tuple[pathlib.Path, int, str]]:
    """(path, line number, line) for every non-ASCII line of an ASCII-only document.

    A line that survives `ascii_fix` is prose, not punctuation: it holds CJK (or another script) and
    has to be written in English. The BOM is reported separately by `stray_boms` because it is not a
    line, and on a pure-ASCII document it is one byte of decoration that has to go.
    """
    found = []
    for path in ascii_only_documents(root):
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.isascii():
                found.append((path, number, line))
    return found


def stray_boms(root: str | pathlib.Path) -> list[pathlib.Path]:
    """ASCII-only documents that carry a BOM: the hint is for non-ASCII text, and this is not that."""
    return [
        path for path in ascii_only_documents(root)
        if path.read_bytes().startswith(BOM)
    ]


def ascii_fix(root: str | pathlib.Path) -> list[pathlib.Path]:
    """Normalise the typographic marks and drop the BOM on every ASCII-only document.

    Returns the files that changed. Idempotent: a document that is already pure ASCII is untouched, so
    this cannot rewrite a file the author just wrote.
    """
    fixed = []
    for path in ascii_only_documents(root):
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        for mark, replacement in ASCII_MARKS:
            text = text.replace(mark, replacement)
        # An em dash typed with spaces around it (" — ") becomes "  -  " the moment the mark is
        # replaced. Those doubled spaces are the conversion's artefact, not the author's, so collapse
        # them - narrowly, around a lone hyphen, because table cells pad with spaces legitimately.
        for _ in range(3):
            text = text.replace("  -  ", " - ").replace("  - ", " - ").replace(" -  ", " - ")
        wanted = text.encode("utf-8")  # no BOM: that is the point of the pure-ASCII bar
        if wanted != raw:
            path.write_bytes(wanted)
            fixed.append(path)
    return fixed
