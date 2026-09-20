"""Live strategy-directive delivery.

The orchestrator's strategy lives in the DIRECTIVE block of the skill file. DeepSeek
Harness reads a skill once, when the agent loads it, so a running session cannot see
a strategy change -- which is why switching strategy used to require a full restart.

This module closes that gap. `take_update()` returns the current directive whenever
it differs from the last one delivered, so `end_turn` can hand it to the agent inside
the tool result it already reads every turn. Switching a preset then takes effect on
the next turn instead of the next session.

It reports on the first call in a process too, which covers a session that started
from a stale skill load.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

# Maintained by scripts/use-strategy.ps1.
_BLOCK = re.compile(
    r"<!-- DIRECTIVE:BEGIN -->(.*?)<!-- DIRECTIVE:END -->", re.DOTALL
)
_DEFAULT_SKILL = Path(".dsh") / "skills" / "civ6-orchestrator" / "SKILL.md"

_last_digest: str | None = None


def skill_path() -> Path:
    override = os.environ.get("CIV_MCP_SKILL_PATH")
    if override:
        return Path(override)
    # The MCP server is launched with the project root as its cwd.
    return Path.cwd() / _DEFAULT_SKILL


def read_directive() -> str | None:
    """Return the current directive body, or None when it cannot be read."""
    try:
        text = skill_path().read_text(encoding="utf-8")
    except OSError:
        return None
    match = _BLOCK.search(text)
    if not match:
        return None
    body = match.group(1).strip()
    return body or None


def take_update() -> str | None:
    """Return a strategy block when the directive changed since the last call.

    Returns None while the directive is unchanged, so a steady strategy costs
    nothing per turn. Resets are not offered: a deleted directive is simply
    reported as no change.
    """
    global _last_digest
    body = read_directive()
    if body is None:
        return None
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if digest == _last_digest:
        return None
    _last_digest = digest
    return (
        "\n\n=== STRATEGY (current; supersedes any earlier strategy instruction) ===\n"
        f"{body}\n"
        "=== END STRATEGY ==="
    )
