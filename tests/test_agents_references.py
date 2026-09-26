"""`AGENTS.md` must not point at a file that is not there.

The reference is the one document every session reads, and it names paths — the tactics table, the
temporary-task directory, the repair scripts, the extracted docs. A rename or a move leaves those
pointers dangling and nothing notices: `test_mcp_tool_registration.py` covers the *tool* names, and this
covers the *paths*. The audit that produced it (2026-09-27) found `prompts/checks/pending/` named by the
camp bullet after the directory had been deleted; it is back with a README, so the instruction is
executable again.

Deliberate exemptions, all about something other than a file in this repository:

* `Base/Assets/...` — the game install's own `Gameplay/Data` and `Text/en_US`;
* placeholders and globs — `<nnn>-<slug>.md`, `…-done-T<turn>.md`, `*.md`, `Base/Assets/**/*.xml`;
* a shorthand like `tactics/07` (no suffix, no separator after the first segment) — the table above it
  names the real files, and those *are* checked.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"

BACKTICK = re.compile(r"`([^`]+)`")
SUFFIXES = (".md", ".py", ".ps1", ".txt", ".json", ".yml", ".yaml", ".lua", ".xml")
# First path segment of a directory this repository owns: enough to treat `prompts/checks/pending/` and
# `.githooks/pre-commit` as paths even though neither ends in a suffix we ship.
ROOT_DIRS = frozenset({
    ".githooks", ".tools", "contracts", "docs", "dsh", "evals", "fixtures", "prompts", "scripts",
    "src", "tests", "web",
})
BARE = frozenset({"AGENTS.md", "SETUP-WINDOWS.md", "README.md"})
PLACEHOLDER = re.compile(r"[<>*…]")
INSTALL = ("Base/", "Base\\")
# References written relative to a directory the sentence itself names: `done/` and `current_tasks.md`
# are the temporary-task directory's, and the procedure says so on the same line. `README.md` resolves at
# the repository root, which exists, so it needs no entry.
RELATIVE = {
    "done": "prompts/tasks/tmp/done",
    "done/": "prompts/tasks/tmp/done",
    "current_tasks.md": "prompts/tasks/tmp/current_tasks.md",
}


def path_tokens() -> list[tuple[str, int]]:
    """Every backticked reference in AGENTS.md that names a path, with the line it is on."""
    out: list[tuple[str, int]] = []
    for number, line in enumerate(AGENTS.read_text(encoding="utf-8-sig").splitlines(), start=1):
        for token in BACKTICK.findall(line):
            token = token.strip()
            if not token or " " in token or PLACEHOLDER.search(token):
                continue
            if token.startswith(INSTALL):
                continue
            if token in BARE or token in RELATIVE:
                out.append((token, number))
                continue
            if "/" not in token and "\\" not in token:
                continue
            rel = token.replace("\\", "/")
            if rel.endswith(SUFFIXES) or rel.endswith("/") or rel.split("/")[0] in ROOT_DIRS:
                out.append((token, number))
    return out


def resolve(token: str) -> pathlib.Path:
    """Where the reference points. The tactics table names its files without the `prompts/` prefix."""
    if token in RELATIVE:
        return ROOT / RELATIVE[token]
    rel = token.replace("\\", "/")
    candidate = ROOT / rel
    if not candidate.exists() and rel.startswith("tactics/"):
        candidate = ROOT / "prompts" / rel
    return candidate


def test_every_path_agents_md_names_exists():
    missing = [(token, line) for token, line in path_tokens() if not resolve(token).exists()]
    assert not missing, (
        "AGENTS.md points at paths that do not exist: "
        + "; ".join(f"line {line}: {token}" for token, line in missing)
    )


def test_the_extractor_is_not_vacuous():
    """A guard against the reference being read as empty text and this test passing for the wrong reason."""
    tokens = path_tokens()
    assert len(tokens) >= 15, f"only {len(tokens)} path references were extracted from AGENTS.md"
    assert any(t.replace("\\", "/").startswith("prompts/") for t, _ in tokens)
    assert any(t.replace("\\", "/").startswith("scripts") for t, _ in tokens)
