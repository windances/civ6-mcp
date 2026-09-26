"""Which text files must carry a UTF-8 BOM, and the one command that puts it back.

A BOM-less UTF-8 file on a Chinese Windows machine is decoded as codepage 936 (GBK) by any editor
that cannot detect the encoding: `游戏应当已经在运行` renders as `娓告垙搴斿綋宸茬粡鍦ㄨ繍琛`. The bytes
are valid UTF-8 and nothing is corrupt - the viewer guessed and guessed wrong. Measured on this repo
on 2026-09-26 for a `.zh.txt` task file, an English one (twelve em dashes), `AGENTS.md`, and the
strategy/tactics documents.

The policy is one line per family: a document holding a non-ASCII byte carries a BOM, an English
`.en.` file is pure ASCII and carries none, and a Chinese `.zh.` file always carries one.

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
