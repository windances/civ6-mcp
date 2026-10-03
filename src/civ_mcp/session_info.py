"""Where this session's records live, said out loud at the start of a run.

Two things decide which stored records a session is reading, and until now neither was ever printed:

* **the data directory** - ``CIV_MCP_DATA_DIR``, defaulting to ``~/.civ6-mcp``. It is the only real
  partition: the diary, ``turn-checks-state.json`` and the heartbeat are all resolved under it *at
  import time*, so a process that sets the variable after importing ``civ_mcp.diary`` reads the
  other directory for the rest of its life.
* **the match key**, ``{civ}_{seed}`` - the diary file name and the retired-goal state key. It
  deliberately does **not** include the run: ``diary_path`` accepts ``run_id`` and ignores it, so a
  restart continues the same diary instead of starting a blank one.

Measured 2026-10-03, and the reason this module exists: the route-A drivers call
``os.environ.setdefault("CIV_MCP_DATA_DIR", <repo>/.civ6-mcp-data)`` at import time, while an
ad-hoc probe that only did ``sys.path.insert(0, "src")`` fell back to ``~/.civ6-mcp``. The same
session then wrote ``turn-checks-state.json`` into one directory and read the diary from the other,
with nothing on screen to say so - ``~/.civ6-mcp`` held the T116 retirement while the 6 MB diary for
the same match sat in ``.civ6-mcp-data``, last written at T76. Every reader that goes to disk
(``get_diary``, the TURN START briefing, the 10-turn review) quoted a position 40 turns old and
looked exactly like a normal read.

So: one line per session, at the two entry points where a turn is judged - ``orient.py`` and
``play-turn.py end`` - naming the directory, the match and the diary's last agent turn. A fork is
then visible on the first call instead of being reconstructed afterwards.

**The diary can be written from a direct session - it just is not automatic.** ``play-turn.py end``
does not append a row (its own comment says so) and ``scripts/record-turn.py --reflections`` is what
does, one turn at a time from the same snapshot. So a stale diary is a missed step, not a missing
capability, and the NOTE line names the step rather than only reporting the gap.
"""

from __future__ import annotations

import os
import pathlib

from civ_mcp import diary as diary_mod
from civ_mcp import run_manifest


def _home() -> pathlib.Path:
    """``Path.home()`` behind a name, so a test can put the *other* directory somewhere harmless.

    ``other_data_dirs`` exists to report the one case that actually bit: the environment variable
    and the home default disagreeing. A test for it must not depend on whatever the developer's
    ``~/.civ6-mcp`` happens to contain.
    """
    return pathlib.Path.home()


def data_dir() -> pathlib.Path:
    """The directory this process is actually using, resolved the way the modules do it."""
    return pathlib.Path(os.environ.get("CIV_MCP_DATA_DIR", _home() / ".civ6-mcp"))


def other_data_dirs() -> list[pathlib.Path]:
    """The other places a session's records might be, for the split-directory warning.

    Only the default is probed: a session either uses ``CIV_MCP_DATA_DIR`` or the home default, and
    the interesting case is precisely those two disagreeing. A third directory can only come from
    an explicit setting, which is already visible in the line this module prints.
    """
    mine = data_dir().resolve()
    default = (_home() / ".civ6-mcp").resolve()
    if mine == default:
        return []
    return [default]


def diary_facts(civ: str, seed: int) -> dict:
    """What the diary for this match holds, without pretending to read a game.

    Returns ``last_turn`` (0 when there is no row), ``rows``, ``agent_rows`` and ``path``. A missing
    file is an ordinary answer, not an error: a match whose diary has never been written is exactly
    the case this line exists to make visible.
    """
    path = diary_mod.diary_path(civ, seed)
    facts = {"path": path, "exists": path.exists(), "rows": 0, "agent_rows": 0, "last_turn": 0}
    if not path.exists():
        return facts
    try:
        entries = diary_mod.read_diary_entries(path)
    except Exception:  # noqa: BLE001 - an unreadable diary is reported as empty, never fatal
        return facts
    facts["rows"] = len(entries)
    agent = [e for e in entries if e.get("is_agent") and isinstance(e.get("turn"), int)]
    facts["agent_rows"] = len(agent)
    if agent:
        facts["last_turn"] = max(e["turn"] for e in agent)
    return facts


def banner(civ: str, seed: int, live_turn: int | None = None) -> list[str]:
    """The SESSION line, plus a warning line only when there is something to warn about."""
    where = data_dir()
    key = f"{civ}_{seed}"
    facts = diary_facts(civ, seed)
    if facts["exists"]:
        diary = (
            f"last_agent_turn={facts['last_turn'] or 'none'} "
            f"rows={facts['rows']}/{facts['agent_rows']}agent"
        )
    else:
        diary = "absent"
    lines = [f"SESSION  data_dir={where}  match={key}  diary={diary}"]

    behind = None
    if live_turn and facts["last_turn"] and live_turn > facts["last_turn"]:
        behind = live_turn - facts["last_turn"]
    if behind:
        lines.append(
            f"NOTE     the diary is {behind} turn(s) behind the live game "
            f"(last T{facts['last_turn']}, live T{live_turn}) - get_diary and the TURN START "
            f"briefing will quote T{facts['last_turn']}; `scripts/record-turn.py --reflections` "
            f"is what writes the missing rows"
        )
    elif live_turn and not facts["last_turn"]:
        lines.append(
            f"NOTE     no diary row for this match - every reader that goes to disk has nothing to "
            f"quote, and the turn checks fall back to the live snapshot. `scripts/record-turn.py "
            f"--reflections` writes one"
        )

    for other in other_data_dirs():
        state = other / "turn-checks-state.json"
        if not state.exists():
            continue
        try:
            text = state.read_text(encoding="utf-8")
        except OSError:
            continue
        if key in text:
            lines.append(
                f"WARNING  {other} also holds records for {key} - two data directories are in "
                f"play, and they are NOT the same session's. Check which one wrote last."
            )

    # Which playthrough, and does the loaded game actually belong to it. The data directory says
    # where the records are; the run manifest says whose they are, and the two are not the same
    # claim: a session can point at the right directory and the wrong game.
    lines.extend(run_manifest.lines(civ, seed))
    return lines


def print_banner(civ: str, seed: int, live_turn: int | None = None) -> None:
    for line in banner(civ, seed, live_turn):
        print(line)
