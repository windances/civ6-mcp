#!/usr/bin/env python3
"""Extract one military-production attempt's numbers from the raw record.

An *attempt* is one played match.  Its raw record is two files the loop already writes:

    .civ6-mcp-data/diary_<game>.jsonl   one snapshot row per player per turn (the economy)
    .civ6-mcp-data/log_<game>_*.jsonl   one row per tool call, with the tool's own reply text
                                        (the rules that failed, the orders that were refused,
                                        the city that was taken)

Nothing here is new instrumentation: the point is that the two files already hold every number an
attempt is judged on, and this turns them into the same table every time, so two attempts can be
compared without re-deriving anything by hand.

    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432
    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432 --step 10 --json
    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432 --verdict
    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432 --run <session> --save A1.json
    .venv\\Scripts\\python.exe scripts/experiment-report.py --compare A1.json A2.json
    .venv\\Scripts\\python.exe scripts/experiment-report.py --list

**Attempts share a game key, because they start from the same save** - so they also share the diary
file, and each attempt overwrites the turn rows the last one wrote. `--save` snapshots an attempt's
numbers while it is still the current one, `--compare` reads those snapshots, and `--run` keeps one
session's log rows when the log family holds several attempts.

Reported, per attempt:

  * the 10-turn economy table (science/culture/gold/pop/districts/wonders/improvements/...)
  * the military table - unit composition at each boundary, so the establishment's growth is visible
  * **the establishment** - the first turn the army matches `prompts/tactics/01-unit-production.md`'s
    table, checked on every turn rather than on the tenth, plus the first turn each role existed;
    this is one of the two numbers the attempt is judged on, and it is measured here rather than
    taken from the session's own account of itself
  * **the verdict** - the A1 predictions in `docs/experiments/001-attempt-A1.md`, answered from the
    record (`--verdict` prints only this)
  * **the production orders** - what the empire *asked for*, from the log's `set_city_production`
    and `purchase_item` calls: the first order in each category and the first turn a siege unit was
    ordered. The diary holds what the empire **has** and the log holds what it **chose**, and the
    doctrine is a claim about the choosing
  * **the doctrine checks** - the claims in `prompts/tactics/01` a log can settle without a judgement
    call: H5 (no ram and no tower is ever bought), H6 (how many cities were asked for units), H4
    (upgrades against new builds) and H1/H2 (the order the roles were asked for). Plus the diary's own
    `ESTABLISHMENT:` line beside the record's numbers, so a self-report the record does not support is
    visible as a MISMATCH instead of being read as fact
  * the capture line - which turn a city was kept, from the tool reply, not from the prose
  * the rule table - `CHECK FAILED [id]` counts, i.e. which doctrine rules the attempt violated
  * the refusal table - STOPPED_MID_PATH and friends, i.e. what the orders cost
  * the process table - tool calls per turn (the attempt's own cost)
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / ".civ6-mcp-data"

# The economy columns, in the order they are worth reading.  Every one of them is a field the diary
# already stores per turn (see civ_mcp.diary); the list is short on purpose.
ECONOMY = (
    "science",
    "culture",
    "gold",
    "gold_per_turn",
    "faith",
    "military",
    "pop",
    "cities",
    "districts",
    "wonders",
    "improvements",
    "territory",
    "techs_completed",
    "civics_completed",
    "tourism",
    "era_score",
)

REFUSALS = (
    "STOPPED_MID_PATH",
    "STOPPED_SHORT",
    "BLOCKED",
    "NO_MOVES",
    "ZOC",
    "TOO FAR",
    "NO_LOS",
    "ERR:",
)

CAPTURE_RE = re.compile(r"\b(KEEP|RAZE|LIBERATE_FOUNDER|LIBERATE_PREVIOUS)\|", re.I)
#: A capture the game **resolved itself**. Measured on A4 at T65: the melee unit's move answered
#: `CAPTURE_MOVE|50,22|...|CITY TAKEN - resolve keep/raze with city_action`, and every
#: `resolve_city_capture(action="keep")` after it answered `NO_PENDING_CITY` - because there was no
#: decision left to make. The city was ours (the next `get_cities` read three cities and the new city
#: accepted production orders), so a reader that only looked for `KEEP|` would score the attempt as
#: having kept nothing. The move's own line is the evidence, and it is matched here.
CAPTURE_TAKEN_RE = re.compile(r"CAPTURE_MOVE\|[^\n]{0,120}?CITY TAKEN", re.I)
#: The city an estimate is aimed at, named in the line that says the target tile is a city:
#: `** Target tile is a city (Jerusalem) ...`. Used with a later `get_cities` row to catch a capture
#: the game reported nowhere (A7 at T60 - a melee attack took the city with no `KEEP|` and no
#: `CAPTURE_MOVE`, and the only evidence is that the next city list counts it as ours).
CITY_ATTACKED_RE = re.compile(r"is a city \(([^)]{1,40})\)")
RULE_RE = re.compile(r"CHECK FAILED \[([a-z0-9\-]+)\]")
ACHIEVED_RE = re.compile(r"CHECK ACHIEVED[^\n]*?\[([a-z0-9\-]+)\]")
ORDER_RE = re.compile(r'"item_name":\s*"([A-Za-z_0-9]+)"')

# The required establishment, as roles rather than unit names: a role is filled by whatever member of
# its upgrade line the era allows, so the same check reads correctly in the Ancient era and in the
# Industrial one.
#
# **Corrected 2026-09-29, after the A2 experiment, to match `prompts/tactics/01-unit-production.md`**:
# the ram left the required table (the same file forbids buying one, so its slot made "complete"
# unsatisfiable - A2 read `siege 2/2, ram 0/1` at its best moment), and `recon` and `anticav` entered it
# (`tactics/07`'s Gate 0 needs a candidate city *seen* and its walls read, which A2 spent twenty-six
# turns unable to do with no scout; and `counter-the-cavalry` was red for A2's whole assault because
# nothing could answer the Heavy Chariot parked next to both Catapults).
# Snapshots taken before this date keep the table they were measured with, which is why the two
# attempts' saved reports still compare on identical terms.
ESTABLISHMENT = {"siege": 2, "melee": 2, "anticav": 1, "ranged": 4, "cavalry": 1, "recon": 1}

#: The roles the *diary's* `ESTABLISHMENT:` line named, in the order it named them, under the task files
#: A1 and A2 were played with (`siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1`). Kept as the record
#: of that historical shape and read by nothing: the parser below takes whatever role tokens a line
#: carries, because the corrected table made the ram conditional and added `anticav` and `recon`, and a
#: parser tied to this tuple would have made every line written from A3 on unreadable.
SELF_REPORT_FIELDS = ("siege", "melee", "ram", "ranged", "cavalry")
ROLES: dict[str, tuple[str, ...]] = {
    "siege": ("CATAPULT", "TREBUCHET", "BOMBARD", "ARTILLERY", "ROCKET_ARTILLERY"),
    "melee": (
        "WARRIOR",
        "SWORDSMAN",
        "MAN_AT_ARMS",
        "MUSKETMAN",
        "LINE_INFANTRY",
        "INFANTRY",
        "MECHANICAL_INFANTRY",
    ),
    "anticav": ("SPEARMAN", "PIKEMAN", "PIKE_AND_SHOT", "AT_CREW", "MODERN_AT"),
    "ram": ("BATTERING_RAM", "SIEGE_TOWER"),
    "ranged": ("SLINGER", "ARCHER", "CROSSBOWMAN", "FIELD_CANNON", "CROUCHING_TIGER"),
    # The game's own CAVALRY tag (`Units.xml`, the `UNITTYPE_*` rows; its `FormationClass` column is
    # only AIR/CIVILIAN/LAND_COMBAT/NAVAL/SUPPORT and too coarse for this table). HEAVY_CHARIOT is the
    # one this map was missing and the case that found it: A2 built one, so the establishment's
    # cavalry slot read 0/1 with a Heavy Chariot standing in the army - and the executor's own
    # "cavalry 1" was scored as a mismatch against a map that could not see the unit.
    # The game's MELEE tag is *not* a discriminator - it also carries HORSEMAN, KNIGHT and the naval
    # melee line - so this line stays the curated upgrade chain.
    "cavalry": (
        "HEAVY_CHARIOT",
        "HORSEMAN",
        "COURSER",
        "KNIGHT",
        "CUIRASSIER",
        "CAVALRY",
        "TANK",
        "MODERN_ARMOR",
        "HELICOPTER",
    ),
    "recon": ("SCOUT", "RANGER", "SKIRMISHER"),
}


# --------------------------------------------------------------------------- raw record


def games() -> list[str]:
    """Every game key that has a diary, newest first."""
    out = []
    for path in DATA.glob("diary_*.jsonl"):
        key = path.stem[len("diary_") :]
        out.append((path.stat().st_mtime, key))
    return [key for _, key in sorted(out, reverse=True)]


def _epoch(stamp: object) -> float | None:
    """A diary row's ISO timestamp as epoch seconds; `None` when the row does not carry one.

    The log's `ts` is already epoch seconds and the diary's `timestamp` is an ISO string in UTC, so
    attribution has to put the two on one scale before it can compare them.
    """
    if isinstance(stamp, (int, float)):
        return float(stamp)
    if not isinstance(stamp, str):
        return None
    try:
        return datetime.datetime.fromisoformat(stamp).timestamp()
    except ValueError:
        return None


def diary_candidates(game: str) -> dict[int, list[dict]]:
    """Every agent row per turn, in file order. A turn may have several: attempts share the key.

    A game with no diary yet - a match that has just been created and not played - is not an error:
    it is an attempt with no rows, and the caller prints exactly that.
    """
    path = DATA / f"diary_{game}.jsonl"
    out: dict[int, list[dict]] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not row.get("is_agent"):
                continue
            turn = row.get("turn")
            if isinstance(turn, int):
                out.setdefault(turn, []).append(row)
    return out


def diary_rows(game: str) -> dict[int, dict]:
    """The agent's own rows, keyed by turn (last write per turn wins).

    That is the right answer for the attempt currently playing and the **wrong** answer for an
    earlier one once a later attempt has played the same turns - see `diary_rows_for_run`.
    """
    return {turn: rows[-1] for turn, rows in diary_candidates(game).items()}


def run_turn_windows(game: str, run: str) -> dict[int, tuple[float, float]]:
    """Each turn of one session, as the epoch range its own log rows span.

    FireTuner serves one connection at a time, so a session's calls do not interleave with another
    session's - which is what makes time a usable stand-in for the session id a diary row lacks.
    """
    windows: dict[int, tuple[float, float]] = {}
    for row in log_rows(game, run):
        turn, ts = row.get("turn"), row.get("ts")
        if not isinstance(turn, int) or not isinstance(ts, (int, float)):
            continue
        lo, hi = windows.get(turn, (float(ts), float(ts)))
        windows[turn] = (min(lo, float(ts)), max(hi, float(ts)))
    return windows


#: Two diary rows for one turn this close to the session's own window cannot be told apart. Guessing
#: would put one attempt's economy in the other's table, so the turn is named and left out instead.
AMBIGUOUS_SECONDS = 120.0

#: How long after its own turn's calls a session may still be writing that turn's diary row, and
#: therefore the only rows that turn may be attributed to. Measured: A2's T40 row landed 22s after the
#: last call of its T40 (whose window was then 2s wide), while the gap between A1's last call and A2's
#: first was 449s - so a row minutes away is another session's, and attributing it is what read A1's
#: T40 economy (science 7.9, military 139) into A2's snapshot when A2's own row said 5.9 and 156.
ATTRIBUTION_SLACK_SECONDS = 120.0


def attribute_diary(
    candidates: dict[int, list[dict]],
    windows: dict[int, tuple[float, float]],
    span: tuple[float, float] | None = None,
) -> tuple[dict[int, dict], list[int]]:
    """One session's diary rows, recovered by time; returns them and the turns that cannot be.

    A diary row carries no session, and attempts share the game key, so after a later attempt plays
    the same turns the file holds two agent rows per turn and last-write-per-turn hands the later
    attempt's numbers to the earlier one. That is not hypothetical: re-reading A1 after A2 had
    reached T10 reported A2's military 31/tourism 0/era 4 where A1's row said 34/8/2, under A1's name.

    Each row is assigned to the turn's own window when the log has one (a session resumed after
    another played the same turns), to the session's overall span otherwise. A turn is only attributed
    when one row is **inside** that window (within `ATTRIBUTION_SLACK_SECONDS`); a row that is merely
    the nearest is another session's, and the turn is named instead - reading the nearest row
    regardless of distance is how A2's first T40 snapshot came out with A1's economy in it.
    """
    by_turn: dict[int, dict] = {}
    unattributed: list[int] = []
    for turn, rows in candidates.items():
        window = windows.get(turn) or span
        if window is None:
            unattributed.append(turn)
            continue
        lo, hi = window
        scored: list[tuple[float, dict]] = []
        for row in rows:
            at = _epoch(row.get("timestamp"))
            if at is None:
                continue
            distance = lo - at if at < lo else (at - hi if at > hi else 0.0)
            scored.append((distance, row))
        if not scored:
            unattributed.append(turn)
            continue
        scored.sort(key=lambda pair: pair[0])
        if scored[0][0] > ATTRIBUTION_SLACK_SECONDS:
            unattributed.append(turn)
            continue
        if len(scored) > 1 and scored[1][0] - scored[0][0] < AMBIGUOUS_SECONDS:
            unattributed.append(turn)
            continue
        by_turn[turn] = scored[0][1]
    return by_turn, sorted(unattributed)


def diary_rows_for_run(game: str, run: str) -> tuple[dict[int, dict], list[int]]:
    """One session's rows even after another attempt overwrote the same turns in the shared diary.

    `run` may name **several sessions**, because an attempt can span a resume: A2's first half is
    `sacred-garnet-vault-35` (T1-T40) and its second half `pale-pearl-aqueduct-92` (T41 on), so a report
    that can only name one of them starts at T41 and drops the other thirty-nine turns. Each named
    session gets its own per-turn windows and its own span, and a row is attributed to whichever named
    session it is closest to - the spans stay separate on purpose, so widening the search to two
    sessions does not widen any single window.
    """
    runs = [part.strip() for part in str(run).split(",") if part.strip()]
    sessions: list[tuple[dict[int, tuple[float, float]], tuple[float, float] | None]] = []
    for name in runs:
        windows = run_turn_windows(game, name)
        span = None
        if windows:
            span = (min(lo for lo, _ in windows.values()), max(hi for _, hi in windows.values()))
        sessions.append((windows, span))
    if len(sessions) == 1:
        return attribute_diary(diary_candidates(game), *sessions[0])
    return attribute_diary_multi(diary_candidates(game), sessions)


def _distance_to_window(at: float, window: tuple[float, float]) -> float:
    """0 when the stamp is inside the window, else the seconds to its nearest edge."""
    lo, hi = window
    return lo - at if at < lo else (at - hi if at > hi else 0.0)


def attribute_diary_multi(
    candidates: dict[int, list[dict]],
    sessions: list[tuple[dict[int, tuple[float, float]], tuple[float, float] | None]],
) -> tuple[dict[int, dict], list[int]]:
    """Attribute each turn to the nearest of **several** sessions of one attempt.

    The gate is unchanged from `attribute_diary` - a row must be inside some named session's window
    (its per-turn window when it has one, else that session's own span), within
    `ATTRIBUTION_SLACK_SECONDS` - but the candidate is scored against its best session rather than a
    single one. Two rows a session apart still cannot be told apart at the same distance, so the turn
    is named instead of guessed.
    """
    by_turn: dict[int, dict] = {}
    unattributed: list[int] = []
    for turn, rows in candidates.items():
        windows = [per_turn.get(turn) or span for per_turn, span in sessions]
        windows = [window for window in windows if window is not None]
        if not windows:
            unattributed.append(turn)
            continue
        scored: list[tuple[float, dict]] = []
        for row in rows:
            at = _epoch(row.get("timestamp"))
            if at is None:
                continue
            scored.append((min(_distance_to_window(at, window) for window in windows), row))
        if not scored:
            unattributed.append(turn)
            continue
        scored.sort(key=lambda pair: pair[0])
        if scored[0][0] > ATTRIBUTION_SLACK_SECONDS:
            unattributed.append(turn)
            continue
        if len(scored) > 1 and scored[1][0] - scored[0][0] < AMBIGUOUS_SECONDS:
            unattributed.append(turn)
            continue
        by_turn[turn] = scored[0][1]
    return by_turn, sorted(unattributed)



def log_rows(game: str, run: str | None = None) -> list[dict]:
    """Every logged call for the game, oldest first. `run` keeps the named sessions' rows only.

    Attempts share a game key: they start from the same save, so the seed - and therefore
    `diary_<game>.jsonl` and the log family - is the same for all of them. A log row carries the
    session that made it, so an attempt's log rows are separable even though its diary rows are not.

    `run` is comma separated because an attempt can span a resume (A2: `sacred-garnet-vault-35` for
    T1-T40, `pale-pearl-aqueduct-92` from T41), and both halves are the same attempt.
    """
    wanted = [part.strip() for part in str(run).split(",") if part.strip()] if run else []
    rows: list[dict] = []
    for path in sorted(DATA.glob(f"log_{game}_*.jsonl")):
        if wanted and not any(name in path.name for name in wanted):
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if wanted:
                    session = row.get("session") or row.get("run_id") or ""
                    if session and session not in wanted:
                        continue
                rows.append(row)
    rows.sort(key=lambda r: r.get("ts") or 0)
    return rows


# --------------------------------------------------------------------------- tables


def _first_turn(by_turn: dict[int, dict]) -> int:
    return min(by_turn) if by_turn else 1


def _last_turn(by_turn: dict[int, dict]) -> int:
    return max(by_turn) if by_turn else 1


def _turn_list(turns: list[int], limit: int = 8) -> str:
    """`T4, T5, T6` for a message; a long run of turns is abbreviated rather than wrapped."""
    head = ", ".join(f"T{turn}" for turn in turns[:limit])
    return f"{head} and {len(turns) - limit} more" if len(turns) > limit else head


def boundaries(by_turn: dict[int, dict], step: int) -> list[int]:
    """One **recorded** turn near each multiple of `step`, plus the first and the last.

    A diary can have gaps - turns nobody played, or turns a rollback removed - so the boundary is the
    first recorded turn at or after each multiple, never the multiple itself. Asking for T240 when no
    row exists at T240 is how this function used to raise `KeyError: 240`.
    """
    turns = sorted(by_turn)
    if not turns:
        return []
    picked = {turns[0], turns[-1]}
    start = ((turns[0] // step) + 1) * step
    for multiple in range(start, turns[-1] + 1, step):
        candidate = next((turn for turn in turns if turn >= multiple), None)
        if candidate is not None:
            picked.add(candidate)
    return sorted(picked)


def economy_table(by_turn: dict[int, dict], step: int) -> list[dict]:
    rows = []
    for turn in boundaries(by_turn, step):
        row = by_turn[turn]
        entry = {"turn": turn}
        for key in ECONOMY:
            entry[key] = row.get(key)
        entry["units_total"] = row.get("units_total")
        entry["trade"] = row.get("trade_routes")
        entry["exploration_pct"] = row.get("exploration_pct")
        rows.append(entry)
    return rows


def deltas(by_turn: dict[int, dict]) -> dict[str, object]:
    """Total and per-turn change between the first and last turn of the attempt."""
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    a, b = by_turn[first], by_turn[last]
    span = max(1, last - first)
    total: dict[str, float] = {}
    per_turn: dict[str, float] = {}
    for key in ECONOMY:
        try:
            delta = float(b.get(key) or 0) - float(a.get(key) or 0)
        except (TypeError, ValueError):
            continue
        total[key] = round(delta, 2)
        per_turn[key] = round(delta / span, 3)
    return {"span": span, "total": total, "per_turn": per_turn}


def composition(by_turn: dict[int, dict], step: int) -> list[tuple[int, dict]]:
    rows = []
    for turn in boundaries(by_turn, step):
        comp = by_turn[turn].get("unit_composition") or {}
        rows.append((turn, comp))
    return rows


def role_counts(comp: dict | None) -> dict[str, int]:
    """Unit types to the establishment's roles. Civilians and great people fall out on the floor."""
    counts = {role: 0 for role in ROLES}
    for unit, number in (comp or {}).items():
        name = str(unit).upper()
        for role, types in ROLES.items():
            if name in types:
                counts[role] += int(number or 0)
                break
    return counts


def establishment(by_turn: dict[int, dict]) -> dict:
    """The first turn the army matches the table, or how short it stood on the last turn read.

    Every turn is checked, not every tenth: the number this returns is one of the two the attempt is
    judged on, and a ten-turn table cannot see a table that filled on T47.
    """
    last_turn: int | None = None
    short: dict[str, tuple[int, int]] = {}
    for turn in sorted(by_turn):
        counts = role_counts(by_turn[turn].get("unit_composition"))
        short = {r: (counts[r], need) for r, need in ESTABLISHMENT.items() if counts[r] < need}
        last_turn = turn
        if not short:
            return {"turn": turn, "counts": counts, "short": {}, "last_turn": turn}
    counts = role_counts(by_turn[last_turn].get("unit_composition")) if last_turn else {}
    return {"turn": None, "counts": counts, "short": short, "last_turn": last_turn}


def first_role_turn(by_turn: dict[int, dict], role: str) -> int | None:
    """The first turn the empire owned any unit of that role - the weakest form of 'it exists'."""
    for turn in sorted(by_turn):
        if role_counts(by_turn[turn].get("unit_composition")).get(role):
            return turn
    return None


# --------------------------------------------------------------------------- production orders
#
# The diary says what the empire *has*; the log says what it *asked for*. The doctrine is a claim
# about the order of the asking ("anything the assault is missing, first"), so the requests are the
# measurement and the inventory is only the cross-check.

ORDER_TOOLS = ("set_city_production", "purchase_item")
ORDER_CATEGORIES = {"UNIT": "units", "DISTRICT": "districts", "BUILDING": "buildings",
                    "PROJECT": "projects", "WONDER": "wonders"}


def unit_type_of(item_name: str) -> str:
    """`UNIT_CROUCHING_TIGER` -> `CROUCHING_TIGER`; anything else passes through unchanged."""
    name = str(item_name or "").upper()
    return name[len("UNIT_"):] if name.startswith("UNIT_") else name


def role_of_item(item_name: str) -> str | None:
    unit = unit_type_of(item_name)
    for role, types in ROLES.items():
        if unit in types:
            return role
    return None


def _order_entries(rows: list[dict]) -> list[tuple[int, str, str, str]]:
    """Every production order and purchase, as (turn, item_name, item_type, city_id).

    `orders()` is this with the city dropped; the pin check needs the city, because two cities can
    order the same unit on the same turn (A2 ordered a Catapult in each on T48) and the opening is
    about which order came when, not about which city placed it. The ordering rules are `orders()`'.
    """
    out: list[tuple[int, str, str, str]] = []
    for row in rows:
        if row.get("tool") not in ORDER_TOOLS:
            continue
        params = row.get("params") or {}
        name = params.get("item_name") or params.get("item") or ""
        if not name:
            match = ORDER_RE.search(json.dumps(params, ensure_ascii=False))
            name = match.group(1) if match else ""
        if name:
            out.append(
                (
                    row.get("turn") or 0,
                    str(name).upper(),
                    str(params.get("item_type") or ""),
                    str(params.get("city_id") or "?"),
                )
            )
    out.sort(key=lambda entry: entry[0])
    return out


def orders(rows: list[dict]) -> list[tuple[int, str, str]]:
    """Every production order and purchase in the log, as (turn, item_name, item_type).

    Sorted by **turn**, not by timestamp. The log holds every session of the game - including the
    branches a rollback abandoned - so rows from different sessions interleave and a later timestamp
    can carry an earlier turn. "The first siege unit was ordered on T38" has to mean the earliest
    turn, which list order alone does not give.
    """
    return [(turn, name, kind) for turn, name, kind, _city in _order_entries(rows)]


def first_order_turn(rows: list[dict], role: str, since: int | None = None) -> int | None:
    """The first turn a unit of that role was *ordered* - the doctrine's own quantity.

    `since` keeps only orders placed on or after that turn, which is what a claim about *ordering after
    a tech* needs: the same siege order can be the answer or irrelevant depending on which side of the
    gate it falls.
    """
    for turn, name, _kind in orders(rows):
        if since is not None and turn < since:
            continue
        if role_of_item(name) == role:
            return turn
    return None


#: The opening the attempt's task file pins, from A3 on: the first four production orders, in order
#: (`prompts/tasks/tmp/NNN-*.md`, "the attempt's record says whether the executor matched them"). It is
#: a promise about the **executor**, and until now it was prose with no mechanical anchor: A3's file was
#: published with this pin and the fourth order placed was `UNIT_WARRIOR` on T15, with the pin in force
#: and no mention of it in the diary. A snapshot from now on carries the fact.
PIN_OPENING = ("UNIT_SCOUT", "UNIT_SLINGER", "UNIT_SETTLER", "UNIT_BUILDER")


def pin_check(rows: list[dict]) -> dict:
    """Whether the first four production orders match the opening the task file pinned.

    `matched` is true only when all four positions **exist and agree**: with fewer than four orders in
    the log the pin is undecided, not held, and the note says what has been placed and that the rest is
    undecided - reporting a two-order log as "matched" would be a claim the record cannot support. The
    comparison is on the item name through `unit_type_of`, so `UNIT_SCOUT` and `SCOUT` are the same
    order, and a deviation names the order that broke the pin with its turn.

    It reads the rows it is given, so a report narrowed to one session of an attempt (`--run`) reads
    that session's opening: an attempt's snapshot names every session it was played in, which is what
    makes the check the attempt's own.
    """
    placed = [(turn, name, city) for turn, name, _kind, city in _order_entries(rows)[:4]]
    promised = PIN_OPENING
    first_deviation: tuple[int, str] | None = None
    deviated_at: int | None = None
    for index, (turn, name, _city) in enumerate(placed):
        if unit_type_of(name) != unit_type_of(promised[index]):
            first_deviation = (turn, name)
            deviated_at = index
            break
    matched = len(placed) >= len(promised) and first_deviation is None
    if deviated_at is not None:
        note = (
            f"opening order {deviated_at + 1} was {first_deviation[1]} on T{first_deviation[0]}, "
            f"not {promised[deviated_at]} - the pin did not hold"
        )
    elif matched:
        note = "the pinned opening held: " + ", ".join(promised) + " in that order"
    else:
        placed_text = ", ".join(f"{name} T{turn}" for turn, name, _city in placed) or "(none)"
        note = (
            f"only {len(placed)} of {len(promised)} opening orders placed so far ({placed_text}) - "
            f"the rest is undecided"
        )
    return {
        "promised": list(promised),
        "orders": placed,
        "placed": len(placed),
        "matched": matched,
        "first_deviation": first_deviation,
        "note": note,
    }


#: The game's own turn-start figures, as `get_game_overview` prints them. Three lines of the reply
#: carry the three numbers an attempt's horizon comparison is made of:
#:   Gold: 96 (+71/turn) | Income: 99 | Maintenance: -28 (units: 15) | Science: 60.9 | ...
#:   Cities: 3 | Population: 28 | Units: 18 -- ...
#: The gold figure is the **net** one (`Income` minus `Maintenance`), which is what the diary's own
#: `gold_per_turn` is, so the two sources are comparable rather than merely similar.
OVERVIEW_SCIENCE_RE = re.compile(r"Science:\s*([\d.]+)")
OVERVIEW_GPT_RE = re.compile(r"Gold:\s*\d+\s*\(\+?([\d.]+)/turn\)")
OVERVIEW_POP_RE = re.compile(r"Population:\s*(\d+)")


def overview_economy(rows: list[dict], turn: int) -> dict | None:
    """The log's own `get_game_overview` figures for one turn, or None if the log has no read of it.

    **Why this exists**: the horizon comparison reads the diary's per-ten-turn row, and an attempt that
    ends **at the start of** its horizon turn never writes one - the session retires on reaching the
    turn and stops before the row exists. Measured in A8 at T110: its row is absent, A7's is present,
    and the claim's discriminating comparison read `OPEN` with nothing to distinguish "not measured
    yet" from "measured and lost". The game's own overview carries the same three numbers and is in
    the attempt's own log, which is the record of the attempt, so it is read as the fallback and the
    reader says which source it used.

    Last read of the turn wins: a turn can be read more than once as it is re-planned.
    """
    found: dict | None = None
    for row in rows:
        if row.get("tool") != "get_game_overview":
            continue
        if (row.get("turn") or 0) != turn:
            continue
        text = f"{row.get('result') or ''}\n{row.get('result_summary') or ''}"
        science = OVERVIEW_SCIENCE_RE.search(text)
        gpt = OVERVIEW_GPT_RE.search(text)
        pop = OVERVIEW_POP_RE.search(text)
        if not (science and gpt and pop):
            continue
        found = {
            "turn": turn,
            "science": float(science.group(1)),
            "gold_per_turn": float(gpt.group(1)),
            "pop": float(pop.group(1)),
        }
    return found


#: The game's own acknowledgement of a purchase (`civ_mcp/lua/cities.py:929`, the MCP strips `OK:`).
#: The reply a refused `purchase_item` gives carries the item's name but never this word, which is why
#: the reader keys on it rather than on the call's parameters.
PURCHASED_RE = re.compile(r"PURCHASED\|")


def siege_purchases(rows: list[dict]) -> list[tuple[int, str]]:
    """Every **bought** siege unit in the log, as (turn, item_name), earliest first.

    A6's variable is that the train is paid for with gold instead of produced, so only `purchase_item`
    rows count: a `set_city_production` of the same unit is exactly the thing the variable replaces, and
    counting it would report the train as bought whether or not a coin was spent.

    **And only a purchase the game acknowledged counts** (`PURCHASED|`, `civ_mcp/lua/cities.py`). A
    refused call carries the same `item_name` in its params as the one that works, so keying on the
    params alone reads a failure as a purchase: measured in A8 at T59, where `purchase_item` answered
    `STACKING_CONFLICT` because the Catapult the city had just built was standing on the city tile, and
    the retry one call later bought it for 320g - the report read that as **two** Catapults bought.
    """
    out: list[tuple[int, str]] = []
    for row in rows:
        if row.get("tool") != "purchase_item":
            continue
        params = row.get("params") or {}
        name = str(params.get("item_name") or "").upper()
        if role_of_item(name) != "siege":
            continue
        said = f"{row.get('result') or ''}\n{row.get('result_summary') or ''}"
        if not PURCHASED_RE.search(said):
            continue
        out.append((row.get("turn") or 0, name))
    out.sort(key=lambda entry: entry[0])
    return out


#: A city we FOUNDED, as the game's own acknowledgement prints it. `CANNOT_FOUND` is the refusal and
#: deliberately does not match: the two appear one turn apart in every attempt that settled a second
#: city (T20 refusal, T21 founded), so a loose `FOUND` match would count the refusal as a city.
FOUNDED_RE = re.compile(r"FOUNDED\|")


def settlements(rows: list[dict]) -> list[tuple[int, str]]:
    """Every city this log **founded**, as (turn, "x,y"), earliest first.

    A8's variable is the number of *settled* cities, which is why this reads `found_city` and not the
    diary's `cities` count: three of the programme's three-city attempts (A3, A4, A7) reached three
    cities by **capturing** one, and a count that cannot tell founding from conquest would score A8's
    variable as already tested when it never was.
    """
    out: list[tuple[int, str]] = []
    for row in rows:
        if row.get("tool") != "unit_action":
            continue
        params = row.get("params") or {}
        if "found_city" not in json.dumps(params):
            continue
        result = str(row.get("result") or "")
        if "CANNOT_FOUND" in result or not FOUNDED_RE.search(result):
            continue
        match = re.search(r"FOUNDED\|([\d,]+)", result)
        out.append((row.get("turn") or 0, match.group(1) if match else "?"))
    out.sort(key=lambda entry: entry[0])
    return out


#: The game's own acknowledgement of a declaration: `src/civ_mcp/lua/diplomacy.py` prints
#: `OK:WAR_REQUESTED|...` on the player operation that declares the war. Deliberately narrow - A2's
#: three calls answered `WARN:WAR_UNCERTAIN` and changed nothing, so this reads the game's own reply.
WAR_RE = re.compile(r"WAR_REQUESTED")


def war_declared(rows: list[dict]) -> int | None:
    """The earliest turn the log holds the game's own war-declaration reply, or None.

    This reads the reply, not an inference: nothing here guesses a war from a `NOT_AT_WAR` refusal, from
    a `WARN:WAR_UNCERTAIN` warning, or from an enemy appearing in the diary - only a row whose `result`
    carries `WAR_REQUESTED` is a declaration, and its earliest turn is the turn the war opened.
    """
    turns = [
        row.get("turn") or 0
        for row in rows
        if WAR_RE.search(str(row.get("result") or "").upper())
    ]
    return min(turns) if turns else None


def engineering_gate(by_turn: dict[int, dict], rows: list[dict]) -> dict:
    """A2's Q2, measured: after Engineering lands, is the siege train ordered before economy?

    A2's question is about the **order of asking after a tech**, and none of the four generic
    predictions is: the closest (A1's P1, "a siege unit early") asks about a calendar deadline and
    reports this attempt's T48 as late. The record's facts are the tech's landing turn, the first siege
    order after it, and the first building or district order after it.

    Returns `status` in the instrument's vocabulary: HELD when the siege order came first or nothing
    else has been ordered yet, FALSIFIED when an economy order came first, OPEN when Engineering has
    not landed inside the attempt.
    """
    landed = next(
        (turn for turn in sorted(by_turn) if "TECH_ENGINEERING" in (by_turn[turn].get("techs") or [])),
        None,
    )
    if landed is None:
        return {
            "status": OPEN,
            "detail": f"Engineering has not landed by T{_last_turn(by_turn)}, so the order is unaskable",
            "engineering_turn": None,
        }
    siege = first_order_turn(rows, "siege", since=landed)
    economy = next(
        (
            turn
            for turn, _name, kind in orders(rows)
            if turn >= landed and kind.upper() in ("BUILDING", "DISTRICT")
        ),
        None,
    )
    if siege is None and economy is None:
        return {
            "status": OPEN,
            "detail": f"Engineering landed T{landed}; neither the siege train nor an economy order has "
                      f"been placed since",
            "engineering_turn": landed,
        }
    if siege is not None and (economy is None or siege <= economy):
        return {
            "status": HELD,
            "detail": f"Engineering T{landed}; first siege order T{siege}"
                      + (f", first economy order T{economy}" if economy is not None else ", no economy order since"),
            "engineering_turn": landed,
        }
    return {
        "status": FALSIFIED,
        "detail": f"Engineering T{landed}; economy order T{economy} came before the first siege order "
                  f"({'T' + str(siege) if siege is not None else 'none'})",
        "engineering_turn": landed,
    }


def verdict_a2(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> list[tuple[str, str, str]]:
    """A2's four questions as A2 wrote them (`docs/experiments/002-attempt-A2.md`).

    Its Q1 is the establishment deadline (the generic slot 2), its Q2 is the ordering after Engineering
    (not a generic slot at all), and Q3/Q4 are the generic slots 3 and 4 - so relabelling the generic
    four by position would put A2's Q1 on the "siege early by T45" line. This answers the four the
    attempt asked, in its own order, from the same record.
    """
    generic = {
        slot: (name, status, detail)
        for slot, (name, status, detail) in zip(
            ("P1", "P2", "P3", "P4"),
            verdict(by_turn, rows, expect_est, expect_city, expect_gold_red),
            strict=True,
        )
    }
    gate = engineering_gate(by_turn, rows)
    return [
        (f"Q1 establishment complete by T{expect_est}", generic["P2"][1], generic["P2"][2]),
        ("Q2 the siege train ordered before any economy order after Engineering", gate["status"], gate["detail"]),
        (f"Q3 first enemy city kept by T{expect_city}", generic["P3"][1], generic["P3"][2]),
        (f"Q4 gold floor red on <{expect_gold_red} turns", generic["P4"][1], generic["P4"][2]),
    ]


#: An attack reply reports a city's walls as `walls: {hp}/{max}` when there are any, and `walls: none`
#: when there are not (`game_state.py`, the branch that reports the city pool whether or not it has
#: walls). A3's whole question is whether that number was ever above zero.
WALL_RE = re.compile(r"walls:\s*(\d+)\s*/\s*(\d+)")

#: A3's window, written from its own queue in task 034: A2 kept its (unwalled) city on T68, and the
#: attempt's late bound is T80. A walled city kept before the early bound falsifies the claim that the
#: wall phase changes the arithmetic - nothing slowed down.
A3_EARLY_KEEP = 68
A3_LATE_KEEP = 80


def wall_phase(by_turn: dict[int, dict], rows: list[dict]) -> dict:
    """A3's Q2, measured: was there a wall to break, and how many turns did it take?

    The wall pool is read off the attack replies, which print `|city hp: N/M, walls: W/M` for a walled
    city and `walls: none` for an unwalled one - so this is the one question the record can answer with
    a number rather than an impression, and A2 could not answer it at all (`walls: none` on every shot).

    Status: HELD when a city with a wall pool was breached and kept inside A3's window, FALSIFIED when
    one was kept outside it, **UNASKABLE once the attempt is over and nothing with a wall pool was ever
    attacked** - the design's own falsifier calls that case "unaskable - report the reads", which is a
    finding about the map rather than a miss - and OPEN while the attempt is still live with no walled
    read yet. The distinction is the point: a finished attempt whose Q2 still reads OPEN looks undecided,
    and the answer it actually produced is that the question could not be asked here.
    """
    reads: list[tuple[int, int, int]] = []
    for row in rows:
        for match in WALL_RE.finditer(row.get("result") or ""):
            hp, top = int(match.group(1)), int(match.group(2))
            if top > 0:
                reads.append((row.get("turn") or 0, hp, top))
    keep = min((turn for turn, _ in captures(rows)), default=None)
    last = _last_turn(by_turn)
    out = {
        "first_wall_turn": None,
        "walls_down_turn": None,
        "keep_turn": keep,
        "reads": len(reads),
    }
    if not reads:
        # **A keep is not what closes this question.** A3's own capture was of an unwalled city and its
        # brief does not end there - it keeps hunting for a walled target to T110 - so treating "a city
        # was kept" as terminal would close Q2 while the attempt was still looking. What closes it is the
        # question's own late bound, T80: past that, no walled target was found inside the window the
        # design gave the attempt, and that is the unaskable answer.
        ended = last >= A3_LATE_KEEP
        out.update(
            status=UNASKABLE if ended else OPEN,
            detail=f"no city with a wall pool above zero was attacked by T{last} - the wall phase is "
                   f"unaskable on this map, which is the attempt's own answer to give"
                   + (f" (the T{A3_LATE_KEEP} bound has passed, so this is the answer and not a window "
                      f"still open)" if ended else ""),
        )
        return out
    first_wall = min(turn for turn, _hp, _top in reads)
    breached = min((turn for turn, hp, _top in reads if hp == 0 and turn >= first_wall), default=None)
    out.update(first_wall_turn=first_wall, walls_down_turn=breached)
    if keep is None:
        out.update(
            status=OPEN,
            detail=f"walls first read above zero on T{first_wall}"
                   + (f", breached T{breached}" if breached is not None else ", not yet breached")
                   + f"; no city kept by T{last}",
        )
        return out
    if keep < A3_EARLY_KEEP:
        out.update(
            status=FALSIFIED,
            detail=f"walls first read T{first_wall}"
                   + (f", breached T{breached}" if breached is not None else "")
                   + f", city kept T{keep} - earlier than T{A3_EARLY_KEEP}, so the wall phase did not "
                     f"slow anything",
        )
        return out
    if keep > A3_LATE_KEEP:
        out.update(
            status=FALSIFIED,
            detail=f"walls first read T{first_wall}"
                   + (f", breached T{breached}" if breached is not None else "")
                   + f", city kept T{keep} - later than T{A3_LATE_KEEP}",
        )
        return out
    out.update(
        status=HELD,
        detail=f"walls first read T{first_wall}"
               + (f", breached T{breached}" if breached is not None else ", breach not read")
               + f", city kept T{keep} - inside the T{A3_EARLY_KEEP}-T{A3_LATE_KEEP} window",
    )
    return out


def verdict_a3(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> list[tuple[str, str, str]]:
    """A3's four questions (task 034, `docs/experiments/README.md`'s A3 row).

    Q1 is the establishment deadline under the corrected table, **Q2 is the wall phase** - the
    measurement no attempt has had - and Q3/Q4 are the generic slots 3 and 4, answered the same way.
    """
    generic = {
        slot: (name, status, detail)
        for slot, (name, status, detail) in zip(
            ("P1", "P2", "P3", "P4"),
            verdict(by_turn, rows, expect_est, expect_city, expect_gold_red),
            strict=True,
        )
    }
    wall = wall_phase(by_turn, rows)
    return [
        (
            f"Q1 establishment complete by T{expect_est} (corrected table)",
            generic["P2"][1],
            generic["P2"][2],
        ),
        ("Q2 a walled target changes the arithmetic measurably", wall["status"], wall["detail"]),
        (f"Q3 first enemy city kept by T{expect_city}", generic["P3"][1], generic["P3"][2]),
        (f"Q4 gold floor red on <{expect_gold_red} turns", generic["P4"][1], generic["P4"][2]),
    ]


def order_summary(rows: list[dict]) -> dict:
    """The first order in each category, and how many of each the attempt made."""
    counts: collections.Counter = collections.Counter()
    firsts: dict[str, tuple[int, str]] = {}
    for turn, name, kind in orders(rows):
        category = ORDER_CATEGORIES.get(kind.upper(), kind.lower() or "other")
        counts[category] += 1
        firsts.setdefault(category, (turn, name))
    return {"counts": dict(counts), "firsts": firsts, "total": sum(counts.values())}


# --------------------------------------------------------------------------- doctrine checks
#
# `prompts/tactics/01-unit-production.md` makes claims a log can settle without a judgement call:
# a unit that is forbidden to buy, a role that must be asked for first, a city count, an upgrade
# count. They are counts rather than opinions about a turn, which is what makes them checkable.

FORBIDDEN_UNITS = ("BATTERING_RAM", "SIEGE_TOWER")  # H5, human instruction 2026-09-26

#: The army half of the establishment table, in one place: H6's concentration claim and A7's "two war
#: cities" both count *army orders*, and recon is not the army - a Scout is `tactics/07`'s Gate 0, not
#: the war's.
ARMY_ROLES = frozenset(role for role in ESTABLISHMENT if role != "recon")


def forbidden_orders(rows: list[dict]) -> list[tuple[int, str, str]]:
    """Every order or purchase of a unit the doctrine forbids - each one violates H5."""
    return [
        (turn, name, kind)
        for turn, name, kind in orders(rows)
        if unit_type_of(name) in FORBIDDEN_UNITS
    ]


def military_city_spread(rows: list[dict]) -> dict:
    """H6's claim is **concentration**, so the honest measure is the share, not the city count.

    `tactics/08` says "one war city; everything else compounds". A1 was first measured as the number of
    distinct cities that ever ordered a unit, which reported two at T30 - the capital with seven orders
    and the second city with one - and read as a violation when the attempt had simply built a single
    unit outside the capital. The count cannot tell concentration from a rounding error.

    What is reported now: the army orders per city (roles in the establishment, plus anti-cavalry -
    recon and civilians are not the army), the busiest city's **share** of them, and the cities where
    army orders are at least half of everything that city was asked to build. The old count is kept in
    `cities` so an attempt's history stays comparable across this change.
    """
    army_roles = ARMY_ROLES  # recon is not the army; H6 is about army production
    army_per_city: collections.Counter = collections.Counter()
    all_per_city: collections.Counter = collections.Counter()
    for row in rows:
        if row.get("tool") not in ORDER_TOOLS:
            continue
        params = row.get("params") or {}
        city = str(params.get("city_id") or "?")
        all_per_city[city] += 1
        if str(params.get("item_type") or "").upper() != "UNIT":
            continue
        if role_of_item(params.get("item_name") or "") in army_roles:
            army_per_city[city] += 1
    total = sum(army_per_city.values())
    busiest_city, busiest = army_per_city.most_common(1)[0] if army_per_city else (None, 0)
    war_cities = sorted(
        city for city, count in army_per_city.items() if count * 2 >= all_per_city[city]
    )
    return {
        "cities": len(army_per_city),  # the old, blunt count - kept so past attempts stay comparable
        "per_city": dict(army_per_city),
        "all_orders_per_city": dict(all_per_city),
        "total_army_orders": total,
        "busiest_city": busiest_city,
        "busiest_share": round(busiest / total, 3) if total else 0.0,
        "war_cities": war_cities,
    }


def _army_orders_by_city(rows: list[dict], before_turn: int | None = None) -> dict[str, list[int]]:
    """City id -> the turns it was asked for an army-role unit, earliest first.

    `before_turn` keeps only orders placed **strictly before** it, which is what makes a second war city
    a claim about the war rather than about the peace that followed it.
    """
    out: dict[str, list[int]] = collections.defaultdict(list)
    for row in rows:
        if row.get("tool") not in ORDER_TOOLS:
            continue
        params = row.get("params") or {}
        if str(params.get("item_type") or "").upper() != "UNIT":
            continue
        if role_of_item(params.get("item_name") or "") not in ARMY_ROLES:
            continue
        turn = row.get("turn") or 0
        if before_turn is not None and turn >= before_turn:
            continue
        out[str(params.get("city_id") or "?")].append(turn)
    return {city: sorted(turns) for city, turns in out.items()}


def army_producing_cities(rows: list[dict], before_turn: int | None = None) -> dict[str, int]:
    """How many army-role unit orders each city was asked for - A7's per-city measure.

    Only `UNIT` orders in the establishment's army roles count (recon and civilians are not the army),
    only cities with at least one such order appear, and `before_turn` counts strictly earlier turns
    only: A7's claim is that two cities were producing **before the first city was kept**, so a city
    that starts after the keep is not a second war city.
    """
    return {city: len(turns) for city, turns in _army_orders_by_city(rows, before_turn).items()}


def upgrades(rows: list[dict]) -> list[tuple[int, str]]:
    """`upgrade_unit` calls in turn order - H4's 'an old unit plus gold is a new unit'."""
    out = [
        (row.get("turn") or 0, str((row.get("params") or {}).get("unit_id") or ""))
        for row in rows
        if row.get("tool") == "upgrade_unit"
    ]
    out.sort(key=lambda entry: entry[0])
    return out


def role_order_sequence(rows: list[dict]) -> list[tuple[int, str, str]]:
    """The first turn each role was asked for as a *unit order*, earliest first (H1/H2)."""
    firsts: dict[str, tuple[int, str]] = {}
    for turn, name, kind in orders(rows):
        if str(kind).upper() != "UNIT":
            continue
        role = role_of_item(name)
        if role and role not in firsts:
            firsts[role] = (turn, name)
    return sorted((turn, role, name) for role, (turn, name) in firsts.items())


def first_military_order(rows: list[dict]) -> tuple[int, str] | None:
    """The turn the army began: the first order of any unit that fills a role in the table."""
    for turn, name, _kind in orders(rows):
        if role_of_item(name):
            return (turn, name)
    return None


def contacts(by_turn: dict[int, dict]) -> list[tuple[int, str]]:
    """The turn each rival first appears in the diary's `diplo_states` - first contact, from the record.

    A conquest attempt with no contacts has no target, and the diary records contact itself: the keys
    of `diplo_states` are the civilisations this empire has met. `exploration_pct` (also in the diary)
    says how much of the map is revealed, which is the other half of the same question - an attempt can
    fail P3 for scouting reasons long before it fails for military ones.
    """
    seen: set[str] = set()
    out: list[tuple[int, str]] = []
    for turn in sorted(by_turn):
        names = set((by_turn[turn].get("diplo_states") or {}).keys())
        for name in sorted(names - seen):
            out.append((turn, name))
        seen |= names
    return out


#: The diary's own `ESTABLISHMENT:` line. **Its shape is not fixed any more**, and that is the point:
#: the ram slot is conditional in the corrected table and `anticav`/`recon` are the two roles the
#: correction added, so the reader takes whatever role tokens the line carries instead of demanding the
#: pre-correction five-slot form. The measured cause: the old regex required `ram`, so **a line without
#: it parsed as nothing at all**, and the one cross-check that caught all eleven of A2's mismatches was
#: blind to exactly the two rows the correction introduced. Anecdotally, the briefs had taken to pinning
#: the old shape and reporting the new rows beside it as unscored - a workaround that this removes.
SELF_REPORT_RE = re.compile(
    r"ESTABLISHMENT:\s*(?P<body>[^\n]*?)(?=\s*WAR READY:|\s*ENEMY SEEN:|$)", re.I
)
_SELF_REPORT_ROLE_RE = re.compile(
    r"(?P<role>siege|melee|ram|ranged|cavalry|anti-?cavalry|anticav|recon)"
    r"[\s*_`]*"
    r"(?P<held>\d+)\s*/\s*\d+",
    re.I,
)
_SELF_REPORT_ALIASES = {"anti-cavalry": "anticav", "anti_cavalry": "anticav"}


def self_reports(by_turn: dict[int, dict]) -> list[dict]:
    """The diary's own `ESTABLISHMENT:` lines, beside what the record says for the same turn.

    The pre-correction brief asked for
    `ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>`, and the corrected one
    adds `anticav` and `recon` while making the ram conditional - so this reader takes every
    `role held/target` token the line carries, in any combination, rather than one fixed shape. The
    instrument computes the same numbers from `unit_composition`, so the two can be compared - and a
    claim the record does not support is exactly the failure this check exists to catch. A turn without
    such a line is not a failure: the line is requested every ten turns, not every turn.
    """
    out: list[dict] = []
    for turn in sorted(by_turn):
        text = (by_turn[turn].get("reflections") or {}).get("strategic") or ""
        match = SELF_REPORT_RE.search(text)
        if not match:
            continue
        claimed: dict[str, int] = {}
        for role, held in _SELF_REPORT_ROLE_RE.findall(match.group("body")):
            key = str(role).lower()
            # First occurrence wins: the report's own tokens come first, and the sentence that follows
            # the report is prose - it quotes the *target* table ("the ranged line needs 4/4"), and
            # taking the last occurrence read A2's T11 report of `siege 0/2` as a claim of 2.
            claimed.setdefault(_SELF_REPORT_ALIASES.get(key, key), int(held))
        if not claimed:
            continue
        actual = role_counts(by_turn[turn].get("unit_composition"))
        out.append(
            {
                "turn": turn,
                "claimed": claimed,
                "actual": actual,
                "mismatch": {
                    role: (held, actual.get(role, 0))
                    for role, held in claimed.items()
                    if held != actual.get(role, 0)
                },
            }
        )
    return out


def rule_turns(rows: list[dict]) -> dict[str, list[int]]:
    """Which turns each rule was red on, deduplicated: a turn can be evaluated more than once."""
    out: dict[str, set[int]] = collections.defaultdict(set)
    for row in rows:
        for rule in RULE_RE.findall(json.dumps(row, ensure_ascii=False)):
            out[rule].add(row.get("turn") or 0)
    return {rule: sorted(turns) for rule, turns in sorted(out.items())}


HELD, FALSIFIED, OPEN = "HELD", "FALSIFIED", "OPEN"
#: The design's own vocabulary for a question the map did not let an attempt ask ("unaskable - report the
#: reads"). It is terminal where OPEN would read as "still undecided".
UNASKABLE = "UNASKABLE"


def _status(met: bool, deadline_reached: bool) -> str:
    """A prediction is only falsified once its deadline has passed.

    Without this the report of a one-turn attempt reads `FALSIFIED P2 establishment complete by T60`,
    which is not a judgement - it is a window that has not closed. `OPEN` is what a mid-window review
    needs for "not yet decidable", and it is the difference between a verdict and a progress note.

    This is the shape of an **achievement** - reaching the establishment, keeping a city - where
    meeting the condition settles it early and missing it only matters once the clock runs out.
    """
    if met:
        return HELD
    return FALSIFIED if deadline_reached else OPEN


def _survival_status(exceeded: bool, deadline_reached: bool) -> str:
    """The shape of a **bound**: it is decided when it is broken, and held only when the window closes.

    "Fewer than ten turns under the gold floor before the first city falls" is not held at turn 1
    because nothing has gone wrong yet - it is simply still running.
    """
    if exceeded:
        return FALSIFIED
    return HELD if deadline_reached else OPEN


def gold_floor(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_gold_red: int = 10,
) -> dict:
    """The turns under the +10 gold floor, by the two measures that disagree about it.

    The rule the criterion names is `carrying-capacity`, gated (`when: turn() >= 60` in
    `prompts/checks/turn-checks.md`), so a horizon at or before that gate can only ever report zero red
    turns - and zero is not evidence the army was paid for. Measured on A2: the rule never fired inside
    its window, while `end_turn`'s own 10-turn review printed `carrying capacity: gold/turn +5.0 ...
    BELOW the +10` at T19 and +7.0/+6.0 at T29/T39. The diary's own gold/turn is therefore reported
    beside the rule's count. The horizon is the first city kept, or the attempt's own establishment
    limit while nothing has fallen yet ("before the city falls", not the whole log).

    Returns the raw numbers beside the two strings the generic verdict's P4 prints, so a question set
    that needs the count itself (A6 compares it with A2's) does not have to parse its own prose.
    """
    keep_turn = min((turn for turn, _ in captures(rows)), default=None)
    horizon = keep_turn if keep_turn is not None else expect_est
    carry = [turn for turn in rule_turns(rows).get("carrying-capacity", []) if turn <= horizon]
    covered = [turn for turn in by_turn if turn <= horizon]
    below = sum(1 for turn in covered if (by_turn[turn].get("gold_per_turn") or 0) < 10)
    last = _last_turn(by_turn)
    return {
        "keep_turn": keep_turn,
        "horizon": horizon,
        "red": len(carry),
        "red_turns": carry,
        "covered": len(covered),
        "below": below,
        "status": _survival_status(len(carry) >= expect_gold_red, last >= horizon),
        "detail": f"{len(carry)} red turn(s) by the rule up to T{horizon}; the diary's own gold/turn "
                  f"is below 10 on {below} of those {len(covered)} turn(s)",
    }


def verdict(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
    ids: tuple[str, ...] = ("P1", "P2", "P3", "P4"),
) -> list[tuple[str, str, str]]:
    """The attempt's predictions, answered from the record.

    The defaults are A1's own limits (`docs/experiments/001-attempt-A1.md`): establishment by T60,
    first city kept by T80, fewer than ten turns under the gold floor before the first city falls,
    and a siege unit early. **They are passed in, not baked in** - a later attempt states its own
    numbers, and a window inside an attempt that is not the attempt's end would otherwise be judged
    against limits it was never meant to meet.

    `ids` is the same courtesy for the labels: A1 called its predictions P1-P4 and A2 called its own
    Q1-Q4, so printing one attempt's ids over the other's record puts two names on one prediction.

    P1 asks about the **order**, not the inventory: the doctrine is a claim about what the empire asks
    for, and the log holds that. Ownership is the fallback for a siege unit that was bought or
    inherited rather than queued, and the label says which one answered.
    """
    if len(ids) != 4:
        raise ValueError(f"verdict needs four prediction ids, got {len(ids)}: {ids!r}")
    est = establishment(by_turn)
    cap = captures(rows)
    keep_turn = min((t for t, _ in cap), default=None)
    # The floor's two measures are `gold_floor`'s, so A5/A6/A7 read the same numbers this prints.
    floor = gold_floor(by_turn, rows, expect_est, expect_gold_red)
    owned = first_role_turn(by_turn, "siege")
    ordered = first_order_turn(rows, "siege")
    early = max(1, expect_est * 3 // 4)
    last = _last_turn(by_turn)
    siege_turn = ordered if ordered is not None else owned
    how = "ordered" if ordered is not None else "owned"
    return [
        (
            f"{ids[0]} a siege unit early ({how} one by T{early})",
            _status(bool(siege_turn and siege_turn <= early), last >= early),
            f"first siege unit {how} {'T' + str(siege_turn) if siege_turn else 'never'}",
        ),
        (
            f"{ids[1]} establishment complete by T{expect_est}",
            _status(bool(est["turn"] and est["turn"] <= expect_est), last >= expect_est),
            f"establishment {'T' + str(est['turn']) if est['turn'] else 'not reached by T' + str(est['last_turn'])}",
        ),
        (
            f"{ids[2]} first enemy city kept by T{expect_city}",
            _status(bool(keep_turn and keep_turn <= expect_city), last >= expect_city),
            f"first keep {'T' + str(keep_turn) if keep_turn else 'none'}",
        ),
        (
            f"{ids[3]} gold floor red on <{expect_gold_red} turns",
            floor["status"],
            floor["detail"],
        ),
    ]


# --------------------------------------------------------------------------- A5/A6/A7
#
# The A2 baseline these three attempts are compared against (`docs/experiments/002-attempt-A2.md`,
# `docs/experiments/A2-final.json`), as the numbers the comparisons need. A2's establishment never
# completed under the corrected table, so "5+ turns earlier" is read against the turn its **siege
# train** was complete (T55, two Catapults owned) - the milestone A2 has and A5/A6 aim to beat - its
# first **economy** (building or district) order **after that gate** was T55, the Granary, and it
# declared war at T60. A2's first non-unit order of any kind was a Granary at **T28**, twenty turns
# before Engineering existed; that is not the number A5's Q3 compares against, which is why the measure
# is taken on the same side of the gate.
A2_SIEGE_DONE = 55
A2_FIRST_ECONOMY_ORDER = 55
A2_WAR_OPEN = 60

#: A2's red `carrying-capacity` count, which A6's Q4 is measured against: **10**, the count to T68 in
#: `A2-final.json` and `002-attempt-A2.md` - the whole attempt, which is the same width as A6's own count
#: (the rule is gated `when: turn() >= 60` and A2's log reads red on T59-T68). **`RETRO-2026-09-29.md`'s
#: rule table records 6 for the same rule, and that is not a second measure**: it is the count inside A2's
#: second session's own T41-T65 window, which the retro now says in as many words. An earlier draft of
#: A6's mode used the 6; A6's brief compares against the ten, so this constant does too - the two sides of
#: a comparison have to be the same width or the verdict is about the window rather than the strategy.
A2_CARRY_RED = 10

#: A5's marks: the establishment 5+ turns ahead of A2's T55 (so by T50), and the economy's first
#: non-unit order no more than 5 turns behind A2's T55 (so by T60).
A5_EARLY_SIEGE = 50
A5_ECONOMY_DEADLINE = 60

#: A6's marks: the first siege unit bought by T50, and the war opened by T55 - 5+ turns ahead of A2's
#: T60.
A6_EARLY_SIEGE = 50
A6_WAR_DEADLINE = 55

#: A7's mark: the first city kept by T80 (`docs/experiments/README.md`'s A7 window).
A7_LATE_KEEP = 80

#: A8's own marks, all read out of the merged A7 report before A8 was published (2026-09-30).
#: A7's own `gpt` series is 6.1 at T40, **8.1 at T50**, 4.1 at T60, 2.1 at T70, 24.4 at T80 - so A7
#: crosses the directive's +10 by itself and without any market, which is why the floor is read at a
#: **fixed turn against A7's value there** rather than as a count of turns under a threshold.
A7_GPT_T40 = 6.1
#: The turn the second siege unit has to be in hand when the third city lands on time - twelve turns after
#: A6 bought its first (T46). **The real deadline is derived per run**: `max(A8_SIEGE_DEADLINE, F + 25)`,
#: where `F` is the third city's founding turn, because a purchase cannot be attributed to a market that
#: does not exist yet.
A8_SIEGE_DEADLINE = 58
#: The third city is designed to be founded about T30; a window that reaches T60 with one founding left
#: it undone rather than late, and the deadline is generous on purpose so a slow Settler is not scored as
#: a missing city.
A8_SETTLE_DEADLINE = 60
#: A7's `gold_per_turn` at each ten-turn row, from the merged A7 continuation report (2026-09-30). A8's
#: floor is read **at the same turn** and must be above it, because A7's level is what a market has to
#: beat - and A7's own curve (2.1 -> 24.4 -> 49.0 across T70/T80/T90) is exactly why a *late* reading
#: proves nothing.
A7_GPT_BY_TURN: dict[int, float] = {50: 8.1, 60: 4.1, 70: 2.1, 80: 24.4, 90: 49.0}
#: A7's whole T110 row, read from the merged A7 continuation report once the run reached it
#: (2026-09-30: `science 57.6, pop 25, gold_per_turn 60.0`, with `cities 3`, `districts 9`,
#: `improvements 14` and `wonders 0` - the empire A8 has to beat). Before it was measured this was
#: `None` on purpose: an instrument must not report a comparison whose baseline does not exist.
A7_T110: dict[str, float | None] = {"science": 57.6, "pop": 25.0, "gold_per_turn": 60.0}
#: The directive's own gold floor, printed for context rather than used as the test. Only A4 ever stood
#: above it in the whole programme, and A4's was bought with Pingala's science.
A8_DIRECTIVE_FLOOR = 10.0


def _q1_establishment(
    generic: dict[str, tuple[str, str, str]], rows: list[dict], expect_est: int
) -> tuple[str, str, str]:
    """A5/A6/A7's Q1: the corrected table's deadline, with the pin's state when it was deviated.

    The three new attempts ask the same first question, and an opening that did not match the task
    file's pin makes the number **not comparable** with the attempt it is being compared to - so the pin
    is printed beside the verdict, not only in the doctrine block a reader of the four answers may not
    see. A2's and A3's verdict text is untouched; for A3 the deviation shows in the doctrine block.
    """
    detail = generic["P2"][2] + f"; falsified when T{expect_est} passes with a role still short"
    pin = pin_check(rows)
    if pin["first_deviation"] is not None:
        detail += f"; PIN DEVIATED - {pin['note']}"
    return (
        f"Q1 establishment complete by T{expect_est} (corrected table)",
        generic["P2"][1],
        detail,
    )


def _generic_slots(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int,
    expect_city: int,
    expect_gold_red: int,
) -> dict[str, tuple[str, str, str]]:
    """The four generic slots, keyed by id, so a question set can take the ones it shares."""
    return {
        slot: (name, status, detail)
        for slot, (name, status, detail) in zip(
            ("P1", "P2", "P3", "P4"),
            verdict(by_turn, rows, expect_est, expect_city, expect_gold_red),
            strict=True,
        )
    }


def verdict_a5(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> list[tuple[str, str, str]]:
    """A5's four questions: Magnus in the war city, the chops into units instead of infrastructure.

    One chop-for-units variable. Q1 is the corrected table's deadline, **Q2 is the variable** - the
    establishment 5+ turns ahead of A2's T55 - Q3 is the cost it is expected to pay (the first economy
    order **after the Engineering gate** no more than 5 turns behind A2's T55, which is itself a
    post-gate order), and Q4 is the generic gold floor.
    """
    generic = _generic_slots(by_turn, rows, expect_est, expect_city, expect_gold_red)
    last = _last_turn(by_turn)
    est = establishment(by_turn)

    # Q2 - the variable: the establishment arrives 5+ turns earlier than A2's siege train at T55.
    if est["turn"] is not None:
        q2_status = _status(est["turn"] <= A5_EARLY_SIEGE, True)
        q2_detail = (
            f"the corrected table completed T{est['turn']}, against A2's siege train at "
            f"T{A2_SIEGE_DONE}; held when <= T{A5_EARLY_SIEGE}, falsified by a later turn"
        )
    elif last >= A5_ECONOMY_DEADLINE:
        q2_status = FALSIFIED
        q2_detail = (
            f"no turn to compare: the corrected table never completed by T{est['last_turn']} - A2's "
            f"mark is T{A2_SIEGE_DONE} and T{A5_EARLY_SIEGE} has passed, so nothing arrived early"
        )
    else:
        q2_status = OPEN
        q2_detail = (
            f"no turn to compare yet: the corrected table has not completed by T{est['last_turn']} "
            f"(A2's mark is T{A2_SIEGE_DONE}, the deadline T{A5_EARLY_SIEGE}); open until "
            f"T{A5_ECONOMY_DEADLINE}"
        )

    # Q3 - the cost: the first economy order **after the Engineering gate**, against A2's T55.
    # Post-gate on purpose, and the measure's own history is why it is spelled out: an earlier draft of
    # this mode read "the first non-unit order", which scored A2's **T28 Granary** as its economy answer
    # - an order placed twenty turns before the train's tech existed, and not the choice this question is
    # about. T55 is A2's first building-or-district order *after* its T48 gate; the two only agree if the
    # measure is taken on the same side of the gate.
    gate = engineering_gate(by_turn, rows)
    landed = gate["engineering_turn"]
    economy = next(
        (
            (turn, name)
            for turn, name, kind in orders(rows)
            if landed is not None and turn >= landed and str(kind).upper() in ("BUILDING", "DISTRICT")
        ),
        None,
    )
    if economy is not None:
        q3_status = _status(economy[0] <= A5_ECONOMY_DEADLINE, True)
        q3_detail = (
            f"first economy order after the T{landed} gate: T{economy[0]} ({economy[1]}), against A2's "
            f"T{A2_FIRST_ECONOMY_ORDER}; held when <= T{A5_ECONOMY_DEADLINE}, falsified by a later turn"
        )
    elif landed is None and last >= A5_ECONOMY_DEADLINE:
        q3_status = FALSIFIED
        q3_detail = (
            f"no gate to measure against: Engineering had not landed by T{last}, so there is no "
            f"post-gate economy order to compare (A2's was T{A2_FIRST_ECONOMY_ORDER})"
        )
    elif last >= A5_ECONOMY_DEADLINE:
        q3_status = FALSIFIED
        q3_detail = (
            f"no building or district ordered since the T{landed} gate, by T{last}: "
            f"T{A5_ECONOMY_DEADLINE} has passed with the economy never restarted (A2's first post-gate "
            f"economy order was T{A2_FIRST_ECONOMY_ORDER})"
        )
    else:
        q3_status = OPEN
        q3_detail = (
            f"no economy order yet at T{last}"
            + (f" since the T{landed} gate" if landed is not None else ", and no gate has opened")
            + f"; the deadline is T{A5_ECONOMY_DEADLINE}, against A2's T{A2_FIRST_ECONOMY_ORDER}"
        )

    q4 = generic["P4"]
    return [
        _q1_establishment(generic, rows, expect_est),
        (
            f"Q2 establishment 5+ turns earlier than A2's T{A2_SIEGE_DONE} (by T{A5_EARLY_SIEGE})",
            q2_status,
            q2_detail,
        ),
        (
            f"Q3 the economy behind by <5 turns (first economy order after the gate, by "
            f"T{A5_ECONOMY_DEADLINE})",
            q3_status,
            q3_detail,
        ),
        (
            f"Q4 gold floor red on <{expect_gold_red} turns",
            q4[1],
            q4[2] + f"; falsified when the rule counts {expect_gold_red} or more",
        ),
    ]


def verdict_a6(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> list[tuple[str, str, str]]:
    """A6's four questions: the siege train is bought with gold, not produced.

    Q1 is the corrected table's deadline, **Q2 is the variable** - the first siege unit *bought*, not
    queued - Q3 is the war, expected 5+ turns ahead of A2's T60, and Q4 is the accepted cost: a red
    `carrying-capacity` window **longer** than A2's, which only counts if the war really did open early.
    """
    generic = _generic_slots(by_turn, rows, expect_est, expect_city, expect_gold_red)
    last = _last_turn(by_turn)

    # Q2 - the variable: a purchase row, not a production order.
    purchases = siege_purchases(rows)
    first_buy = purchases[0][0] if purchases else None
    produced = first_order_turn(rows, "siege")
    if first_buy is not None and first_buy <= A6_EARLY_SIEGE:
        q2_status = HELD
        q2_detail = (
            f"the first siege unit was bought T{first_buy} ({purchases[0][1]}), inside "
            f"T{A6_EARLY_SIEGE}; falsified by a later purchase"
        )
    elif first_buy is not None:
        q2_status = FALSIFIED
        q2_detail = (
            f"the first siege purchase is T{first_buy} ({purchases[0][1]}), later than "
            f"T{A6_EARLY_SIEGE}"
        )
    elif produced is not None:
        q2_status = FALSIFIED
        q2_detail = (
            f"a siege unit was ordered on T{produced} and no siege purchase row exists in this log - "
            f"the train was produced, so the variable was not executed"
        )
    elif last >= A6_EARLY_SIEGE:
        q2_status = FALSIFIED
        q2_detail = (
            f"no siege purchase and no siege order by T{last}: T{A6_EARLY_SIEGE} has passed with the "
            f"first siege unit not existing at all"
        )
    else:
        q2_status = OPEN
        q2_detail = (
            f"no siege purchase yet at T{last} - the deadline is T{A6_EARLY_SIEGE}, and a purchase"
            f" later than it, or a produced train with no purchase at all, falsifies the variable"
        )

    # Q3 - the war opens 5+ turns earlier than A2's T60.
    war = war_declared(rows)
    if war is not None:
        q3_status = _status(war <= A6_WAR_DEADLINE, True)
        q3_detail = (
            f"war declared T{war} (the game's own WAR_REQUESTED reply), against A2's T{A2_WAR_OPEN}; "
            f"held when <= T{A6_WAR_DEADLINE}"
        )
    elif last >= A2_WAR_OPEN:
        q3_status = FALSIFIED
        q3_detail = (
            f"no war-declaration row exists in this attempt's log by T{last}: T{A6_WAR_DEADLINE} "
            f"passed and so did A2's own T{A2_WAR_OPEN}, so nothing opened 5 turns earlier"
        )
    else:
        q3_status = OPEN
        q3_detail = (
            f"no war-declaration row exists in this attempt's log yet (T{last}); the deadline is "
            f"T{A6_WAR_DEADLINE} against A2's T{A2_WAR_OPEN}, and T{A2_WAR_OPEN} is where it becomes "
            f"falsified"
        )

    # Q4 - the accepted cost: the red window has to run **longer** than A2's, and the war has to have
    # opened inside the deadline for the trade to be the one that was predicted.
    floor = gold_floor(by_turn, rows, expect_est, expect_gold_red)
    red, horizon = floor["red"], floor["horizon"]
    if war is not None and war > A6_WAR_DEADLINE:
        q4_status = FALSIFIED
        q4_detail = (
            f"the war opened T{war}, later than T{A6_WAR_DEADLINE}, so the predicted trade was never "
            f"made; {floor['detail']}"
        )
    elif war is None and last >= A6_WAR_DEADLINE:
        q4_status = FALSIFIED
        q4_detail = (
            f"no war declaration by T{A6_WAR_DEADLINE}, so the price the variable pays cannot be the "
            f"predicted one; {floor['detail']}"
        )
    elif war is None:
        q4_status = OPEN
        q4_detail = (
            f"no war declaration yet at T{last}, so whether the cost was paid cannot be judged against "
            f"A2's {A2_CARRY_RED} red turn(s); {floor['detail']}"
        )
    elif red > A2_CARRY_RED:
        q4_status = HELD
        q4_detail = (
            f"the war opened T{war} by T{A6_WAR_DEADLINE} and {red} red turn(s) is longer than A2's "
            f"{A2_CARRY_RED}; {floor['detail']}"
        )
    elif last >= horizon:
        q4_status = FALSIFIED
        q4_detail = (
            f"the war opened T{war} by T{A6_WAR_DEADLINE}, but only {red} red turn(s) up to T{horizon} "
            f"- not longer than A2's {A2_CARRY_RED}, so the purchase turned out free; {floor['detail']}"
        )
    else:
        q4_status = OPEN
        q4_detail = (
            f"the war opened T{war} by T{A6_WAR_DEADLINE}; the red window runs to T{horizon} and the "
            f"attempt stands at T{last}, so {red} red turn(s) is not final; {floor['detail']}"
        )

    return [
        _q1_establishment(generic, rows, expect_est),
        (
            f"Q2 the first siege unit bought by T{A6_EARLY_SIEGE} (not produced)",
            q2_status,
            q2_detail,
        ),
        (
            f"Q3 war declared by T{A6_WAR_DEADLINE}, against A2's T{A2_WAR_OPEN}",
            q3_status,
            q3_detail,
        ),
        (
            f"Q4 a red gold-floor window longer than A2's {A2_CARRY_RED} turns",
            q4_status,
            q4_detail,
        ),
    ]


def verdict_a7(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> list[tuple[str, str, str]]:
    """A7's four questions: two war cities instead of one.

    Q1 is the corrected table's deadline, **Q2 is the variable** - two cities each producing an
    army-role unit *before the first city is kept* - Q3 is the first keep by T80, and Q4 is the generic
    gold floor. Q2's pass condition is the count of cities; the stricter share measure is printed beside
    it and deliberately not the pass condition.
    """
    generic = _generic_slots(by_turn, rows, expect_est, expect_city, expect_gold_red)
    last = _last_turn(by_turn)
    keep_turn = min((turn for turn, _ in captures(rows)), default=None)

    # Q2 - the variable: the second city has to contribute before the first city is kept.
    counts = army_producing_cities(rows, keep_turn)
    firsts = {city: turns[0] for city, turns in _army_orders_by_city(rows, keep_turn).items()}
    ordered = sorted(counts, key=lambda city: firsts[city])
    per_city_text = (
        ", ".join(f"city {city} {counts[city]} (first T{firsts[city]})" for city in ordered)
        if ordered
        else "no city has ordered an army-role unit"
    )
    second_text = (
        f"the second city's first army order is T{firsts[ordered[1]]} (city {ordered[1]})"
        if len(ordered) >= 2
        else "there is no second city's first army order to report"
    )
    window = (
        f"orders placed before the keep on T{keep_turn}"
        if keep_turn is not None
        else f"no city was kept by T{last}, so every order in the log counts"
    )
    stricter = military_city_spread(rows)["war_cities"]
    q2_status = _status(len(counts) >= 2, keep_turn is not None or last >= A7_LATE_KEEP)
    q2_detail = (
        f"{per_city_text}; {second_text}; window: {window}; the stricter secondary measure (army "
        f"orders at least half of that city's orders) names "
        f"{', '.join(stricter) if stricter else 'none'} - not the pass condition"
    )

    # Q3 - the first city is kept by T80.
    if keep_turn is not None:
        q3_status = _status(keep_turn <= A7_LATE_KEEP, True)
        q3_detail = (
            f"the first city was kept T{keep_turn} (the reply's own capture line); held when <= "
            f"T{A7_LATE_KEEP}, falsified by a later keep"
        )
    elif last >= A7_LATE_KEEP:
        q3_status = FALSIFIED
        q3_detail = (
            f"no keep row in this attempt's log by T{last}: T{A7_LATE_KEEP} has passed with no city "
            f"taken"
        )
    else:
        q3_status = OPEN
        q3_detail = f"no keep row yet at T{last}; the deadline is T{A7_LATE_KEEP}"

    q4 = generic["P4"]
    return [
        _q1_establishment(generic, rows, expect_est),
        (
            "Q2 two cities produce army units before the first city is kept",
            q2_status,
            q2_detail,
        ),
        (
            f"Q3 the first city kept by T{A7_LATE_KEEP}",
            q3_status,
            q3_detail,
        ),
        (
            f"Q4 gold floor red on <{expect_gold_red} turns",
            q4[1],
            q4[2] + f"; falsified when the rule counts {expect_gold_red} or more",
        ),
    ]


def verdict_a8(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
    a7_t110: dict[str, float | None] | None = None,
) -> list[tuple[str, str, str]]:
    """A8's four questions: three cities settled, and whether the settled third one pays.

    Q1 is the corrected table's deadline, **Q2 is the variable** - the empire **founded** a third city -
    Q3 is the **second** siege unit in hand by its deadline **and bought rather than built**, and Q4 is the
    gold clause: the floor read at its turn, **and** A8's T110 `science`/`pop`/`gold_per_turn` against A7's.

    **Both of Q3's and Q4's turns are derived from the third city's founding turn `F`, not the calendar.**
    The purchase deadline is `max(A8_SIEGE_DEADLINE, F+25)`; the floor is read at **T50 if `F <= 28`**,
    otherwise at the first ten-turn row at or after `F+22`. That is the arithmetic the attempt was recut
    for: the only pre-flight read was taken with **three** cities standing, so it could not see the sites a
    two-city position leaves open, and the far site it named is about **20 tiles** from the capital - a
    third city founded around T48 rather than T30, whose Market cannot exist by T50. **A claim whose
    deadlines move has to derive them from the run, and the run has to fix `F` in the diary the turn it
    happens.**

    Q2 counts `found_city`, not the diary's `cities`: the capital is already standing in the shared start,
    so three cities is **two** foundings, and a `cities` count could not tell founding from conquest - A3,
    A4 and A7 all reached three cities by **taking** one, which is what A8 exists to do differently. A
    garrison in the new city is expected and is not the variable; the army-order spread is printed beside
    the count so a reader can see whether the third city stayed economic.

    Q4 is deliberately **not** the generic gold-floor count: that counts turns under the directive's +10,
    and A7 crosses it by itself with **no market at all**, so a count ending high would credit the third
    city for the second one's Campus and improvements. The horizon half of Q4 is the number that
    discriminates - **both runs end holding three cities, and the difference is how the third was
    obtained** - and it reads `OPEN` until A7's own T110 row has been measured and put in `A7_T110`,
    because an instrument must not answer a comparison whose baseline does not exist yet. `gpt_T40` is
    printed beside all of it as the draft's own prediction (at or below A7's 6.1), not as a bar.
    """
    a7_t110 = A7_T110 if a7_t110 is None else a7_t110
    generic = _generic_slots(by_turn, rows, expect_est, expect_city, expect_gold_red)
    last = _last_turn(by_turn)

    # Q2 - the variable: cities this empire settled, and the founding turn everything else derives from.
    founded = settlements(rows)
    founding = founded[1][0] if len(founded) >= 2 else None
    spread = military_city_spread(rows)
    busiest = ", ".join(
        f"city {city} {count}"
        for city, count in sorted(spread["per_city"].items(), key=lambda kv: -kv[1])[:4]
    )
    found_text = ", ".join(f"T{turn} at {xy}" for turn, xy in founded) if founded else "none"
    q2_detail = (
        f"foundings beyond the capital: {len(founded)} of 2 ({found_text})"
        + (f"; the third city is the one founded T{founding}" if founding is not None else "")
        + f"; army orders by city, busiest first: {busiest or 'none placed'}"
        + f"; window: no third city by T{A8_SETTLE_DEADLINE} is the falsifier"
    )
    q2_status = _status(len(founded) >= 2, last >= A8_SETTLE_DEADLINE)

    # Both of the claim's turns come out of `F` - the recut's whole point.
    deadline = max(A8_SIEGE_DEADLINE, founding + 25) if founding is not None else A8_SIEGE_DEADLINE
    if founding is None or founding <= 28:
        floor_turn = 50
    else:
        floor_turn = next((t for t in sorted(A7_GPT_BY_TURN) if t >= founding + 22), None)
    a7_floor = A7_GPT_BY_TURN.get(floor_turn) if floor_turn is not None else None

    # Q3 - the number: the second siege unit in hand by its deadline, and bought.
    bought = siege_purchases(rows)
    built = [
        row.get("turn") or 0
        for row in rows
        if row.get("tool") == "set_city_production"
        and role_of_item(str((row.get("params") or {}).get("item_name") or "")) == "siege"
    ]
    siege_two = next(
        (
            turn
            for turn in sorted(by_turn)
            if role_counts(by_turn[turn].get("unit_composition")).get("siege", 0) >= 2
        ),
        None,
    )
    bought_in_time = bool(bought) and bought[0][0] <= deadline
    in_hand_in_time = siege_two is not None and siege_two <= deadline
    q3_status = _status(bought_in_time and in_hand_in_time, last >= deadline)
    derived = (
        f"deadline T{deadline}"
        + (f" (max(T{A8_SIEGE_DEADLINE}, F+25) with F=T{founding})" if founding is not None else "")
    )
    q3_detail = (
        f"{derived}"
        f"; bought: {', '.join(f'T{turn} {name}' for turn, name in bought) if bought else 'no siege unit was bought'}"
        f"; built in a city: {', '.join(f'T{turn}' for turn in built) if built else 'none'}"
        f"; the siege row reached 2 on "
        f"{f'T{siege_two}' if siege_two is not None else 'no turn read'}"
        f" - A6 bought its **first** at T46 where A8 produces the first and buys the second, so the two "
        f"purchase columns are not the same act"
    )

    # Q4 - the gold clause: the floor at its own turn, and the horizon trio against A7's.
    row40 = by_turn.get(40)
    gpt40 = row40.get("gold_per_turn") if row40 else None
    t40_text = f"{gpt40:+.1f}" if isinstance(gpt40, (int, float)) else "no T40 row"

    floor_row = by_turn.get(floor_turn) if floor_turn is not None else None
    gpt_floor = floor_row.get("gold_per_turn") if floor_row else None
    floor_ok: bool | None = None
    if isinstance(gpt_floor, (int, float)) and isinstance(a7_floor, (int, float)):
        floor_ok = gpt_floor > a7_floor
    floor_text = (
        f"gpt at T{floor_turn} {gpt_floor:+.1f} against A7's {a7_floor}"
        if floor_ok is not None
        else f"the floor turn T{floor_turn} has no readable row yet"
        if floor_turn is not None
        else f"no ten-turn row at or after T{founding + 22} in A7's table, so the floor turn is not defined"
    )

    keys = ("science", "pop", "gold_per_turn")
    row110 = by_turn.get(110)
    horizon_source = "the diary's T110 row"
    if row110 is None:
        # The attempt may have stopped at the start of T110 and never written the row; the game's own
        # overview is in its log (see `overview_economy`).
        row110 = overview_economy(rows, 110)
        horizon_source = "the log's own T110 `get_game_overview`"
    if row110 is None:
        horizon_source = "no T110 row in the diary and no T110 overview in the log"
    horizon_ok: bool | None = None
    if row110 and all(isinstance(a7_t110.get(k), (int, float)) for k in keys):
        horizon_ok = all(
            isinstance(row110.get(k), (int, float)) and row110[k] > a7_t110[k]  # type: ignore[operator]
            for k in keys
        )
    horizon_text = (
        "; T110 (from " + horizon_source + ") "
        + ", ".join(
            f"{k} {row110.get(k)} vs A7's {a7_t110.get(k)}"
            if isinstance(row110.get(k), (int, float))
            else f"{k} unread vs A7's {a7_t110.get(k)}"
            for k in keys
        )
        if row110 and all(isinstance(a7_t110.get(k), (int, float)) for k in keys)
        else "; T110 not readable yet, or A7's own T110 row has not been measured"
    )

    if floor_ok is False or horizon_ok is False:
        q4_status = FALSIFIED
    elif floor_ok and horizon_ok:
        q4_status = HELD
    else:
        q4_status = OPEN
    q4_detail = (
        f"{floor_text}{horizon_text}; the directive's own floor is {A8_DIRECTIVE_FLOOR:.0f} and only A4 "
        f"ever stood above it in the whole programme, with Pingala's science rather than a market; the "
        f"draft's own prediction is gpt at T40 at or below A7's {A7_GPT_T40} and it read {t40_text} - a "
        f"prediction, not a bar"
    )

    return [
        _q1_establishment(generic, rows, expect_est),
        ("Q2 three cities settled - two foundings beyond the capital", q2_status, q2_detail),
        (
            f"Q3 the second siege unit in hand by T{deadline}, bought not built",
            q3_status,
            q3_detail,
        ),
        (
            "Q4 the gold clause - the floor at its own turn, and the T110 trio against A7's",
            q4_status,
            q4_detail,
        ),
    ]


#: `--questions` names one of the question sets, and each is a function with the same signature.
#: There is deliberately no `a4`: A4 uses A3's question set, because its variable moves the same
#: wall-phase question to a different city.
QUESTION_SETS = {
    "a2": verdict_a2,
    "a3": verdict_a3,
    "a5": verdict_a5,
    "a6": verdict_a6,
    "a7": verdict_a7,
    "a8": verdict_a8,
}


def asked_questions(
    questions: str,
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
    ids: tuple[str, ...] = ("P1", "P2", "P3", "P4"),
) -> list[tuple[str, str, str]]:
    """The question set `--questions` names, answered from the record.

    `generic` is `verdict()` itself - it takes the caller's own `--ids` - and every named set answers
    four questions of its own from the same record, under the same limits.
    """
    setter = QUESTION_SETS.get(questions)
    if setter is None:
        return verdict(by_turn, rows, expect_est, expect_city, expect_gold_red, ids)
    return setter(by_turn, rows, expect_est, expect_city, expect_gold_red)


def print_doctrine(by_turn: dict[int, dict], rows: list[dict]) -> None:
    """The doctrine's mechanical claims, and whether the diary's own account matches the record."""
    print("\n-- doctrine checks (from the log; prompts/tactics/01) --")

    # The pinned opening first: every attempt's numbers are only comparable with the attempt it is
    # compared to if the first four orders are the ones the task file promised.
    pin = pin_check(rows)
    state = "DEVIATED" if pin["first_deviation"] else ("held" if pin["matched"] else "undecided")
    print(f"  PIN opening: {state} - {pin['note']}")

    forbidden = forbidden_orders(rows)
    if forbidden:
        for turn, name, kind in forbidden:
            print(f"  H5 VIOLATED: {name} ordered on T{turn} ({kind}) - no ram and no tower is bought")
    else:
        print("  H5 clean: neither a ram nor a siege tower was ever ordered or bought")

    spread = military_city_spread(rows)
    if spread["cities"]:
        worst = ", ".join(
            f"city {city}: {count}"
            for city, count in sorted(spread["per_city"].items(), key=lambda kv: -kv[1])[:4]
        )
        share = f"{spread['busiest_city']} carries {spread['busiest_share']:.0%} of them"
        print(
            f"  H6 war cities: {spread['cities']} cities ordered army units "
            f"({worst}); {share}"
        )
        print(
            "     war cities (army orders at least half of that city's orders): "
            + (", ".join(spread["war_cities"]) if spread["war_cities"] else "none")
        )
    else:
        print("  H6 war cities: no army unit has been ordered yet")

    ups = upgrades(rows)
    if ups:
        print(f"  H4 upgrades: {len(ups)} upgrade_unit call(s), first on T{ups[0][0]}")
    else:
        print("  H4 upgrades: none")

    sequence = role_order_sequence(rows)
    if sequence:
        print("  H1/H2 the order of asking: " + ", ".join(f"{role} T{turn}" for turn, role, _ in sequence))
    else:
        print("  H1/H2 the order of asking: no role-mapped unit has been ordered yet")

    reports = self_reports(by_turn)
    if not reports:
        print("  self-report: no ESTABLISHMENT line in the diary yet (it is asked for every ten turns)")
    for report in reports:
        if report["mismatch"]:
            detail = ", ".join(
                f"{role} claimed {claimed} vs {actual} held"
                for role, (claimed, actual) in report["mismatch"].items()
            )
            print(f"  self-report T{report['turn']}: MISMATCH - {detail}")
        else:
            print(f"  self-report T{report['turn']}: agrees with the record")


def print_verdict(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
    ids: tuple[str, ...] = ("P1", "P2", "P3", "P4"),
    questions: str = "generic",
) -> None:
    est = establishment(by_turn)
    print("-- establishment (prompts/tactics/01-unit-production.md) --")
    print("  the table: " + "  ".join(f"{role} {need}" for role, need in ESTABLISHMENT.items()))
    if est["turn"]:
        counts = "  ".join(f"{role}={est['counts'].get(role, 0)}" for role in ESTABLISHMENT)
        print(f"  COMPLETE at T{est['turn']}   {counts}")
    else:
        short = "  ".join(f"{role} {have}/{want}" for role, (have, want) in sorted(est["short"].items()))
        print(f"  NOT complete at T{est['last_turn']}   short: {short or '(none)'}")
        if set(est["short"]) == {"recon"}:
            print(
                "    (only recon is missing - and `tactics/07`'s Gate 0 is that a candidate city is "
                "actually visible, with its walls, HP and garrison read; A2 spent twenty-six turns "
                "unable to read any of them because no scout was ever built)"
            )
    print(
        f"  screens (melee + anti-cavalry): "
        f"{est['counts'].get('melee', 0) + est['counts'].get('anticav', 0)}"
        f"   recon: {est['counts'].get('recon', 0)}"
    )
    for role in ESTABLISHMENT:
        turn = first_role_turn(by_turn, role)
        print(f"  first {role:<8s}: {'T' + str(turn) if turn else 'never'}")

    summary = order_summary(rows)
    if summary["total"]:
        print("\n-- production orders (what the empire asked for, from the log) --")
        for category, (turn, name) in sorted(summary["firsts"].items(), key=lambda kv: kv[1][0]):
            print(f"  first {category:<10s}: T{turn:<4} {name}")
        print("  counts: " + "  ".join(f"{k} {v}" for k, v in sorted(summary["counts"].items())))
        ordered = first_order_turn(rows, "siege")
        if ordered is not None:
            print(f"  the siege train was first ordered on T{ordered}")
        first_military = first_military_order(rows)
        if first_military:
            print(f"  the army began on T{first_military[0]} ({first_military[1]})")

    print_doctrine(by_turn, rows)

    met = contacts(by_turn)
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    print("\n-- exploration and contact (the other half of 'can we take a city') --")
    print(
        f"  map revealed: {by_turn[first].get('exploration_pct')}% at T{first} -> "
        f"{by_turn[last].get('exploration_pct')}% at T{last}"
    )
    if met:
        for turn, name in met:
            print(f"  first contact T{turn:<4} {name}")
    else:
        print(f"  no rival met by T{last}: there is no city to aim at yet")

    print(f"\n-- verdict (limits: establishment T{expect_est}, city T{expect_city}, "
          f"gold floor {expect_gold_red}) --")
    results = asked_questions(
        questions, by_turn, rows, expect_est, expect_city, expect_gold_red, ids
    )
    for name, status, detail in results:
        print(f"  {status:<9s} {name}  [{detail}]")
    if any(status == OPEN for _n, status, _d in results):
        print(
            f"  (OPEN means the deadline has not arrived: the attempt stands at "
            f"T{_last_turn(by_turn)}, so those predictions are undecided, not failed)"
        )


def rule_counts(rows: list[dict]) -> tuple[collections.Counter, list[tuple[int, str]]]:
    counts: collections.Counter = collections.Counter()
    achieved: list[tuple[int, str]] = []
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for rule in RULE_RE.findall(blob):
            counts[rule] += 1
        for rule in ACHIEVED_RE.findall(blob):
            achieved.append((row.get("turn") or 0, rule))
    return counts, achieved


def refusal_counts(rows: list[dict]) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for name in REFUSALS:
            n = blob.count(name)
            if n:
                counts[name] += n
    return counts


def captures(rows: list[dict]) -> list[tuple[int, str]]:
    """City keeps/razes, deduplicated - the same reply appears in both `result` and its summary.

    **Three shapes count, because the game produces three.** The explicit one is a `KEEP|`/`RAZE|` reply
    from `city_action`. The second is a `CAPTURE_MOVE` whose own line says `CITY TAKEN`: there the game
    resolved the capture itself, no keep/raze decision was ever pending, and every later
    `resolve_city_capture` answers `NO_PENDING_CITY` - so `KEEP|` never appears even though the city is
    ours (A4 measured that at T65). **The third was measured on A7 at T60 and produces no capture reply
    at all**: a melee attack took the city during the inter-turn, so the log holds neither `KEEP|` nor
    `CAPTURE_MOVE` - the only evidence is that the next `get_cities` row **lists the city as ours**.
    That shape is read here by remembering the cities we have attacked (the estimate's
    `** Target tile is a city (NAME)` line) and looking for those names in later `get_cities` rows;
    a city we attacked appearing in our own city list is a city we hold, whatever the replies said.
    """
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str]] = []
    # Pass 1: the names of every city an estimate named as a target, with the first turn it was named.
    attacked: dict[str, int] = {}
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for match in CITY_ATTACKED_RE.finditer(blob):
            name = match.group(1).strip()
            if name and name not in attacked:
                attacked[name] = row.get("turn") or 0
    # Pass 2: the two reply shapes.
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for pattern in (CAPTURE_RE, CAPTURE_TAKEN_RE):
            for match in pattern.finditer(blob):
                snippet = blob[match.start() : match.end() + 40]
                key = (row.get("turn") or 0, snippet[:28])
                if key in seen:
                    continue
                seen.add(key)
                out.append((row.get("turn") or 0, snippet))
    # Pass 3: a city we attacked that a later city list shows as ours. **Reported once, at the first
    # turn it is seen ours** - a city we hold stays in every later `get_cities` row, so without this the
    # same keep is reported on every turn after it (measured on A7's T110 snapshot: Jerusalem appeared
    # eight times, T60 through T94, which would make a count of captures read 8 for one city).
    reported: set[str] = set()
    for row in rows:
        if row.get("tool") != "get_cities":
            continue
        turn = row.get("turn") or 0
        blob = json.dumps(row, ensure_ascii=False)
        for name, attack_turn in attacked.items():
            if name in reported or turn < attack_turn or f"{name} (pop " not in blob:
                continue
            reported.add(name)
            out.append(
                (turn, f"kept {name} (listed in this turn's get_cities as ours, after being attacked)")
            )
    out.sort(key=lambda pair: pair[0])
    return out


def tool_calls(rows: list[dict]) -> collections.Counter:
    return collections.Counter(row.get("tool") for row in rows)


# --------------------------------------------------------------------------- across attempts
#
# Attempts share a game key, because they start from the same save. That means they share the diary
# file too, and each attempt overwrites the turn rows the last one wrote. **So an attempt's numbers
# have to be snapshotted while it is the current one** (`--save`), and the comparison reads those
# snapshots - not the diary, which by then belongs to whoever played last.


def attempt_row(name: str, payload: dict) -> dict:
    """The comparable columns of one attempt's saved report."""
    economy = {entry.get("turn"): entry for entry in payload.get("economy") or []}

    def at(turn: int) -> dict:
        return economy.get(turn) or {}

    doctrine = payload.get("doctrine") or {}
    establishment = (payload.get("establishment") or {}).get("turn")
    army = doctrine.get("first_military_order")
    sequence = {role: turn for turn, role, _name in (doctrine.get("role_order_sequence") or [])}
    keeps = [entry[0] for entry in (payload.get("captures") or []) if entry]
    mismatches = sum(
        1 for report in (doctrine.get("self_reports") or []) if report.get("mismatch")
    )
    return {
        "attempt": name,
        "turns": f"T{payload.get('first_turn')}-T{payload.get('last_turn')}",
        "establishment": f"T{establishment}" if establishment else "not reached",
        "army_start": f"T{army[0]}" if army else "-",
        "siege_order": f"T{sequence['siege']}" if "siege" in sequence else "never",
        "first_keep": f"T{min(keeps)}" if keeps else "none",
        "sci_T20": at(20).get("science", "-"),
        "sci_T40": at(40).get("science", "-"),
        # Named `gpt`, not `gold`: the economy table's `gold` is the treasury and this is the income.
        # Quoting one for the other read 6 (GPT) against a real 236 (treasury) at A1's T40.
        "gpt_T40": at(40).get("gold_per_turn", "-"),
        "h5": len(doctrine.get("forbidden_orders") or []),
        "self_mismatch": mismatches,
        "rules_red": len(payload.get("rules") or {}),
    }


COMPARE_COLUMNS = (
    "turns",
    "establishment",
    "army_start",
    "siege_order",
    "first_keep",
    "sci_T20",
    "sci_T40",
    "gpt_T40",
    "h5",
    "self_mismatch",
    "rules_red",
)


def print_compare(paths: list[pathlib.Path]) -> int:
    """One line per attempt, from the snapshots `--save` wrote."""
    rows: list[dict] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:  # noqa: PERF203 - one bad file, not a stop
            print(f"  {path}: unreadable ({exc})", file=sys.stderr)
            continue
        rows.append(attempt_row(path.stem, payload))
    if not rows:
        print("nothing to compare", file=sys.stderr)
        return 2
    header = ["attempt"] + list(COMPARE_COLUMNS)
    widths = [max(len(h), *(len(str(r.get(h, "-"))) for r in rows)) for h in header]
    print("  ".join(h.ljust(w) for h, w in zip(header, widths)))
    for row in rows:
        print("  ".join(str(row.get(h, "-")).ljust(w) for h, w in zip(header, widths)))
    print(
        "\ncolumns: establishment = the turn the army matched tactics/01's table; army_start = first "
        "role-mapped unit ordered;\nsiege_order = first siege order; h5 = ram/tower orders (must be 0); "
        "self_mismatch = diary ESTABLISHMENT lines the record contradicts;\nsci_T20/sci_T40/gpt_T40 = "
        "science and gold income **per turn** at that turn (the treasury is `gold` in the economy table)."
    )
    return 0


# --------------------------------------------------------------------------- printing


def print_text(
    game: str,
    step: int,
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
    ids: tuple[str, ...] = ("P1", "P2", "P3", "P4"),
    questions: str = "generic",
) -> None:
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    print(f"== attempt {game}: T{first} -> T{last} ==")
    civ = by_turn[first].get("civ")
    print(f"civ: {civ}  era: {by_turn[last].get('era')}  government: {by_turn[last].get('government')}")

    print("\n-- economy --")
    header = ["turn"] + list(ECONOMY[:8]) + ["districts", "wonders", "improvements"]
    print("  ".join(f"{h:>11s}" for h in header))
    for entry in economy_table(by_turn, step):
        cells = [f"{entry['turn']:>11d}"]
        for key in header[1:]:
            value = entry.get(key)
            cells.append(f"{value:>11}" if value is not None else f"{'-':>11}")
        print("  ".join(cells))

    delta = deltas(by_turn)
    print("\n-- window delta (whole attempt) --")
    print(f"  span: {delta['span']} turns")
    for key, value in delta["total"].items():  # type: ignore[union-attr]
        rate = delta["per_turn"][key]  # type: ignore[index]
        print(f"  {key:>18s}: {value:+9.2f}   ({rate:+.3f}/turn)")

    print("\n-- military composition --")
    for turn, comp in composition(by_turn, step):
        if not comp:
            print(f"  T{turn:<4} (none)")
            continue
        body = ", ".join(f"{name}:{n}" for name, n in sorted(comp.items(), key=lambda kv: -kv[1]))
        print(f"  T{turn:<4} {body}")

    counts, achieved = rule_counts(rows)
    print("\n-- rules (CHECK FAILED counts) --")
    if counts:
        for rule, n in counts.most_common():
            print(f"  {n:>4d}  {rule}")
    else:
        print("  (no failures recorded)")
    if achieved:
        print("  achieved:")
        for turn, rule in achieved:
            print(f"  T{turn:<4} {rule}")

    refusals = refusal_counts(rows)
    print("\n-- refusals --")
    for name, n in refusals.most_common():
        print(f"  {n:>4d}  {name}")

    cap = captures(rows)
    print("\n-- captures --")
    if cap:
        for turn, text in cap:
            print(f"  T{turn:<4} {text.strip()}")
    else:
        print("  (no city captured or kept)")

    calls = tool_calls(rows)
    total = sum(calls.values())
    print("\n-- process --")
    print(f"  tool calls: {total} over {last - first + 1} turns = {total / max(1, last - first + 1):.1f}/turn")
    print("  most used: " + ", ".join(f"{t}:{n}" for t, n in calls.most_common(8)))

    print()
    print_verdict(by_turn, rows, expect_est, expect_city, expect_gold_red, ids, questions)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", help="game key, e.g. china_-1894041591")
    ap.add_argument("--step", type=int, default=10, help="turn step for the tables (default 10)")
    ap.add_argument("--from", dest="start", type=int, help="first turn to report (inclusive)")
    ap.add_argument("--to", dest="end", type=int, help="last turn to report (inclusive)")
    ap.add_argument("--json", action="store_true", help="emit the tables as JSON")
    ap.add_argument("--list", action="store_true", help="list the game keys that have a diary")
    ap.add_argument("--verdict", action="store_true",
                    help="print only the establishment and the verdict")
    ap.add_argument("--expect-est", type=int, default=60,
                    help="the attempt's own establishment deadline, in turns (default 60: A1's)")
    ap.add_argument("--expect-city", type=int, default=80,
                    help="the attempt's own first-city deadline (default 80: A1's)")
    ap.add_argument("--expect-gold-red", type=int, default=10,
                    help="how many turns under the gold floor the attempt allows (default 10: A1's)")
    ap.add_argument("--ids", default="P1,P2,P3,P4",
                    help="the attempt's own prediction labels for the verdict, comma separated "
                         "(default P1,P2,P3,P4: A1's; A2's are Q1,Q2,Q3,Q4)")
    ap.add_argument("--questions", choices=("generic", "a2", "a3", "a5", "a6", "a7", "a8"), default="generic",
                    help="which four questions to answer: the generic P1-P4 slots (default), A2's own "
                         "Q1-Q4 (its Q2 is the ordering after Engineering, which no generic slot "
                         "measures), A3's own Q1-Q4 (its Q2 is the wall phase - whether a city's wall "
                         "pool was ever above zero and how many turns it took to breach), A5's "
                         "(Groundbreaker: a 5+ turn earlier establishment against the economy), A6's "
                         "(the train bought with gold, at the cost of a longer gold-floor window), "
                         "A7's (two war cities before the first keep) or A8's (three cities settled, "
                         "and the second siege unit bought by T58 against the gpt the third city's "
                         "market has to beat). There is deliberately no 'a4': A4 uses A3's question set")
    ap.add_argument("--run", help="keep one or more sessions' rows (comma separated when an attempt "
                                  "spans a resume); attempts share a game key")
    ap.add_argument("--save", help="write this attempt's report to a JSON file, for --compare later")
    ap.add_argument("--compare", nargs="+",
                    help="compare saved attempt reports (files written by --save) and exit")
    args = ap.parse_args()
    args.ids = tuple(part.strip() for part in args.ids.split(",") if part.strip())
    if len(args.ids) != 4:
        print(
            f"--ids needs four labels - one per prediction - not {len(args.ids)}: {','.join(args.ids)}",
            file=sys.stderr,
        )
        return 2

    if args.compare:
        return print_compare([pathlib.Path(p) for p in args.compare])

    if args.list or not args.game:
        for key in games():
            by_turn = diary_rows(key)
            print(f"{key}  T{_first_turn(by_turn)} -> T{_last_turn(by_turn)}  ({len(by_turn)} turns)")
        return 0

    sys.stdout.reconfigure(encoding="utf-8")
    rows = log_rows(args.game, args.run)
    unattributed: list[int] = []
    if args.run:
        # The diary is shared by every attempt on this key and keeps the last write per turn, so a
        # plain read would hand this attempt the later one's economy. Attribute by session time.
        by_turn, unattributed = diary_rows_for_run(args.game, args.run)
    else:
        by_turn = diary_rows(args.game)
    if not by_turn:
        if unattributed:
            print(
                f"no diary row could be attributed to {args.run}: the turns in the file "
                f"({_turn_list(unattributed)}) were written by another session or too close to one",
                file=sys.stderr,
            )
        else:
            print(f"no diary rows for {args.game}", file=sys.stderr)
        return 2
    if unattributed:
        print(
            f"  NOTE: {_turn_list(unattributed)} left out: this session's own row for that turn is not "
            f"in the diary, or two attempts wrote it too close in time to tell apart - no number is "
            f"attributed to {args.run} there.",
            file=sys.stdout,
        )
    if args.start is not None:
        by_turn = {t: r for t, r in by_turn.items() if t >= args.start}
        rows = [r for r in rows if (r.get("turn") or 0) >= args.start]
    if args.end is not None:
        by_turn = {t: r for t, r in by_turn.items() if t <= args.end}
        rows = [r for r in rows if (r.get("turn") or 0) <= args.end]
    if not by_turn:
        print("no diary rows in that turn range", file=sys.stderr)
        return 2

    counts, achieved = rule_counts(rows)
    payload = {
        "game": args.game,
        "run": args.run,
        "first_turn": _first_turn(by_turn),
        "last_turn": _last_turn(by_turn),
        "economy": economy_table(by_turn, args.step),
        "delta": deltas(by_turn),
        "composition": [{"turn": t, "units": c} for t, c in composition(by_turn, args.step)],
        "rules": dict(counts),
        "rule_turns": rule_turns(rows),
        "achieved": achieved,
        "refusals": dict(refusal_counts(rows)),
        "captures": captures(rows),
        "tool_calls": dict(tool_calls(rows)),
        "establishment": establishment(by_turn),
        "contacts": contacts(by_turn),
        "exploration_pct": {
            "first": by_turn[_first_turn(by_turn)].get("exploration_pct"),
            "last": by_turn[_last_turn(by_turn)].get("exploration_pct"),
        },
        "orders": order_summary(rows),
        "doctrine": {
            "forbidden_orders": forbidden_orders(rows),
            "military_city_spread": military_city_spread(rows),
            "upgrades": upgrades(rows),
            "role_order_sequence": role_order_sequence(rows),
            "first_military_order": first_military_order(rows),
            "self_reports": self_reports(by_turn),
        },
        # The pinned opening travels with every snapshot: an attempt whose first four orders are not
        # the promised ones is not comparable with the attempt it is being compared to, and the fact
        # belongs in the record rather than in the prose that asked for the pin.
        "pin": pin_check(rows),
        "verdict": [
            {"prediction": name, "status": status, "detail": detail}
            for name, status, detail in asked_questions(
                args.questions, by_turn, rows, args.expect_est, args.expect_city, args.expect_gold_red,
                args.ids,
            )
        ],
    }

    if args.save:
        out = pathlib.Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {out}  (this attempt's numbers survive the next attempt overwriting the diary)")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.verdict:
        print(f"== attempt {args.game}: T{_first_turn(by_turn)} -> T{_last_turn(by_turn)} ==")
        print_verdict(
            by_turn, rows, args.expect_est, args.expect_city, args.expect_gold_red, args.ids,
            args.questions,
        )
        return 0

    print_text(
        args.game, args.step, by_turn, rows, args.expect_est, args.expect_city, args.expect_gold_red,
        args.ids, args.questions,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
