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
